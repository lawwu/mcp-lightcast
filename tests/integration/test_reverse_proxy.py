"""Real nginx TLS termination and prefix routing, with no live Lightcast traffic."""

import asyncio
import json
import os
import ssl
import subprocess
import time
import uuid
from pathlib import Path

import httpx
import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

pytestmark = pytest.mark.proxy
PROXY_FILES = Path(__file__).resolve().parents[1] / "proxy"
HEADERS = {"Host": "mcp.test", "Origin": "https://client.test"}


@pytest.fixture(scope="module")
def proxy_stack(tmp_path_factory):
    tls = tmp_path_factory.mktemp("proxy-tls")
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(tls / "key.pem"),
            "-out",
            str(tls / "cert.pem"),
            "-days",
            "1",
            "-subj",
            "/CN=mcp.test",
            "-addext",
            "subjectAltName=DNS:mcp.test,IP:127.0.0.1",
            "-addext",
            "basicConstraints=critical,CA:TRUE",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    (tls / "empty.env").write_text("")
    environment = {**os.environ, "PROXY_TLS_DIR": str(tls)}
    compose = [
        "docker",
        "compose",
        "--project-name",
        f"lightcast-proxy-{uuid.uuid4().hex[:12]}",
        "--env-file",
        str(tls / "empty.env"),
        "--file",
        str(PROXY_FILES / "compose.yml"),
    ]

    def run(*args, check=True):
        result = subprocess.run(
            [*compose, *args],
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if check and result.returncode:
            pytest.fail(
                f"Compose {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
            )
        return result.stdout

    try:
        run("up", "--detach")
        address = run("port", "proxy", "8443").strip()
        assert address.startswith("127.0.0.1:"), run("ps", "--all") + run(
            "logs", "--tail", "60"
        )
        url = f"https://{address}"
        verify = ssl.create_default_context(cafile=str(tls / "cert.pem"))
        # Only this freshly allocated loopback port is used for startup polling.
        with httpx.Client(verify=verify, trust_env=False, timeout=2) as client:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    response = client.get(f"{url}/health", headers=HEADERS)
                    if response.status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(0.2)
            else:
                pytest.fail(
                    "Proxy did not become healthy:\n" + run("logs", "--tail", "60")
                )
        yield url, verify
        logs = run("logs")
        for secret in (
            "proxy-test-secret",
            "synthetic-secret-a",
            "synthetic-secret-b",
            "wrong-private-secret",
            "synthetic-token-proxy-test-client",
            "synthetic-token-account-a",
            "synthetic-token-account-b",
        ):
            assert secret not in logs
    finally:
        run("down", "--volumes", "--remove-orphans", check=False)


@pytest.mark.parametrize("prefix", ["", "/lightcast"])
async def test_health_through_tls_proxy(proxy_stack, prefix):
    url, verify = proxy_stack
    async with httpx.AsyncClient(verify=verify, trust_env=False) as client:
        response = await client.get(f"{url}{prefix}/health", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["cache-control"] == "no-store"
        response = await client.head(f"{url}{prefix}/health", headers=HEADERS)
        assert response.status_code == 200 and response.content == b""


@pytest.mark.parametrize("prefix", ["", "/lightcast"])
@pytest.mark.parametrize(
    "mode,protocol", [("auto", "2026-07-28"), ("legacy", "2025-11-25")]
)
async def test_mcp_round_trip_through_tls_proxy(proxy_stack, prefix, mode, protocol):
    url, verify = proxy_stack

    def http_client(**kwargs):
        return httpx2.AsyncClient(verify=verify, trust_env=False, **kwargs)

    transport = StreamableHttpTransport(
        f"{url}{prefix}/mcp",
        headers=HEADERS,
        httpx_client_factory=http_client,
    )
    async with Client(transport, mode=mode, timeout=15) as client:
        assert client.protocol_version == protocol
        tools = await client.list_tools()
        assert len(tools) == 37
        assert "query_core_lmi" in {tool.name for tool in tools}
        info = await client.read_resource("lightcast://server/info")
        assert "Core LMI (Agnitio)" in json.loads(info[0].text)["supported_apis"]
        result = await client.call_tool(
            "query_core_lmi",
            {
                "dataset": "emsi.us.occupation",
                "version": "2026.4",
                "query": {
                    "metrics": [{"name": "Jobs.2025"}],
                    "constraints": [],
                    "limit": 2,
                },
            },
        )
        assert not result.is_error
        assert result.structured_content["data"][0]["rows"] == [42, None]
        assert result.structured_content["version"] == "2026.4"
        assert result.structured_content["pagination"]["returned"] == 2


@pytest.mark.parametrize(
    "headers,status",
    [
        ({"Host": "evil.example", "X-Forwarded-Host": "mcp.test"}, 421),
        ({**HEADERS, "Origin": "https://evil.example"}, 403),
        ({**HEADERS, "Origin": "null"}, 403),
    ],
)
async def test_proxy_does_not_bypass_request_protection(proxy_stack, headers, status):
    url, verify = proxy_stack
    async with httpx.AsyncClient(verify=verify, trust_env=False) as client:
        response = await client.post(
            f"{url}/lightcast/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 1, "method": "server/discover"},
        )
    assert response.status_code == status


@pytest.mark.parametrize("library", [httpx, httpx2])
async def test_proxy_network_exception_never_allows_external_requests(library):
    async with library.AsyncClient(trust_env=False) as client:
        with pytest.raises(AssertionError, match="Unmocked network request"):
            await client.get("https://api.lightcast.io")


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_header_accounts_are_isolated_through_tls_proxy(proxy_stack, mode):
    url, verify = proxy_stack

    def make_client(credentials):
        def http_client(**kwargs):
            return httpx2.AsyncClient(verify=verify, trust_env=False, **kwargs)

        return Client(
            StreamableHttpTransport(
                f"{url}/headers/mcp",
                headers={**HEADERS, **credentials},
                httpx_client_factory=http_client,
            ),
            mode=mode,
            timeout=15,
        )

    async def query(account, secret, expected):
        credentials = (
            {}
            if account is None
            else {
                "X-Lightcast-Client-Id": account,
                "X-Lightcast-Client-Secret": secret,
            }
        )
        async with make_client(credentials) as client:
            result = await client.call_tool(
                "query_core_lmi",
                {
                    "dataset": "emsi.us.occupation",
                    "version": "2026.4",
                    "query": {
                        "metrics": [{"name": "Jobs.2025"}],
                        "constraints": [],
                        "limit": 2,
                    },
                },
                raise_on_error=False,
            )
            if expected is None:
                assert result.is_error
                assert "wrong-private-secret" not in str(result)
            else:
                assert not result.is_error
                assert result.structured_content["data"][0]["rows"] == [expected, None]
                health = await client.read_resource("lightcast://server/health")
                assert json.loads(health[0].text)["authentication"] == "verified"

    await asyncio.gather(
        query("account-a", "synthetic-secret-a", 101),
        query("account-b", "synthetic-secret-b", 202),
    )
    await asyncio.gather(
        query("account-a", "wrong-private-secret", None),
        query(None, None, None),
        query("account-b", "synthetic-secret-b", 202),
    )
    async with httpx.AsyncClient(verify=verify, trust_env=False) as client:
        health = await client.get(f"{url}/headers/health", headers=HEADERS)
        assert health.status_code == 200 and health.json() == {"status": "ok"}
