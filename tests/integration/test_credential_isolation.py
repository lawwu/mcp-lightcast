"""Real MCP dispatch with concurrent HTTP callers and synthetic upstream traffic."""

import asyncio
import json
from contextlib import asynccontextmanager
from urllib.parse import parse_qs

import httpx
import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.dependencies import get_access_token, get_http_request

from mcp_lightcast.auth.credentials import LightcastCredentials
from mcp_lightcast.server import create_server


def headers(account, secret=None):
    return {
        "X-Lightcast-Client-Id": account,
        "X-Lightcast-Client-Secret": secret or f"secret-{account}",
        "Authorization": "Bearer inbound-only-do-not-forward",  # gitleaks:allow -- synthetic inbound token
    }


@asynccontextmanager
async def http_server(provider=None, auth=None):
    app = create_server(provider, auth=auth).http_app(host_origin_protection=True)

    def client(request_headers=None, mode="auto"):
        def factory(**kwargs):
            return httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), **kwargs)

        return Client(
            StreamableHttpTransport(
                "http://127.0.0.1/mcp",
                headers=request_headers or {},
                httpx_client_factory=factory,
            ),
            mode=mode,
        )

    async with app.router.lifespan_context(app):
        yield client


@pytest.fixture
def upstream(httpx_mock):
    calls = []

    async def respond(request):
        await asyncio.sleep(0)
        if request.url.path == "/connect/token":
            fields = parse_qs(request.content.decode())
            account = fields["client_id"][0]
            secret = fields["client_secret"][0]
            scope = fields["scope"][0]
            calls.append(("oauth", account, scope))
            if secret not in {f"secret-{account}", f"rotated-{account}"}:
                return httpx.Response(401, json={"error": f"sensitive: {secret}"})
            return httpx.Response(
                200,
                json={
                    "access_token": f"{account}:{scope}:{secret}",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        assert "x-lightcast-client-secret" not in request.headers
        assert "x-lightcast-client-id" not in request.headers
        assert "inbound-only" not in request.headers["authorization"]
        account, scope, _ = (
            request.headers["authorization"].removeprefix("Bearer ").split(":")
        )
        calls.append(("api", account, scope))
        if account == "refresh" and calls.count(("api", account, scope)) == 1:
            return httpx.Response(401, json={"secret": "private-expired-token"})
        if account == "quota":
            return httpx.Response(429, json={"secret": "private-quota-message"})
        if account == "denied":
            return httpx.Response(403, json={"secret": "private-denial"})
        if request.url.path.endswith("/normalize"):
            return httpx.Response(
                200,
                json={
                    "data": {"title": {"id": account, "name": account}, "confidence": 1}
                },
            )
        if request.url.path.endswith("/extract"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"skill": {"id": account, "name": account}, "confidence": 1}
                    ]
                },
            )
        return httpx.Response(200, json={"data": {"id": account, "name": account}})

    httpx_mock.add_callback(respond, is_reusable=True)
    return calls


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_concurrent_accounts_workflows_resources_and_errors(
    monkeypatch, upstream, mode, caplog
):
    monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "headers")
    async with http_server() as make_client:

        async def request(account):
            async with make_client(headers(account), mode) as client:
                result = await client.call_tool(
                    "analyze_job_posting_skills",
                    {"job_title": "Python", "job_description": "SQL"},
                )
                assert (
                    result.structured_content["normalized_title"]["title"]["id"]
                    == account
                )
                assert result.structured_content["combined_skills"][0]["id"] == account
                health = await client.read_resource("lightcast://server/health")
                assert json.loads(health[0].text)["authentication"] == "verified"

        await asyncio.gather(request("a"), request("b"))
        assert sorted(call for call in upstream if call[0] == "oauth") == [
            ("oauth", "a", "emsi_open"),
            ("oauth", "b", "emsi_open"),
        ]

        async def lookup(account):
            async with make_client(headers(account), mode) as client:
                return await client.call_tool(
                    "get_skill_details", {"skill_id": "KS1"}, raise_on_error=False
                )

        denied, quota, good = await asyncio.gather(
            lookup("denied"), lookup("quota"), lookup("b")
        )
        assert denied.is_error and "403" in denied.content[0].text
        assert quota.is_error and "quota" in quota.content[0].text
        assert not good.is_error and good.structured_content["id"] == "b"
        assert "private-" not in str(denied) + str(quota) + caplog.text
        assert "secret-a" not in caplog.text and "secret-b" not in caplog.text


async def test_wrong_rotated_and_missing_headers_do_not_reuse_cached_token(
    monkeypatch, upstream
):
    monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "headers")
    async with http_server() as make_client:
        for supplied, success in [
            (headers("a"), True),
            (headers("a", "wrong"), False),
            ({}, False),
            (headers("a", "rotated-a"), True),
        ]:
            async with make_client(supplied) as client:
                # Discovery works without credentials; calls requiring Lightcast fail closed.
                assert len(await client.list_tools()) == 37
                result = await client.call_tool(
                    "get_skill_details", {"skill_id": "KS1"}, raise_on_error=False
                )
                assert result.is_error is not success
    assert [call for call in upstream if call[0] == "oauth"] == [
        ("oauth", "a", "emsi_open")
    ] * 3
    assert len([call for call in upstream if call[0] == "api"]) == 2


async def test_custom_provider_resolves_once_for_all_workflow_steps(upstream):
    class AuthorizedProvider:
        def __init__(self):
            self.calls = []

        async def resolve(self):
            # Synthetic identity stands in for a deployment's verified auth claims.
            account = get_http_request().headers["x-test-identity"]
            self.calls.append(account)
            await asyncio.sleep(0)
            return LightcastCredentials(account, f"secret-{account}")

    provider = AuthorizedProvider()
    async with http_server(provider) as make_client:

        async def request(account):
            async with make_client({"X-Test-Identity": account}) as client:
                result = await client.call_tool(
                    "analyze_job_posting_skills",
                    {"job_title": "Python", "job_description": "SQL"},
                )
                assert (
                    result.structured_content["normalized_title"]["title"]["id"]
                    == account
                )

        await asyncio.gather(request("a"), request("b"))
    assert sorted(provider.calls) == ["a", "b"]


async def test_provider_uses_verified_identity_and_rejects_unauthenticated_requests(
    upstream,
):
    class TestVerifier(TokenVerifier):
        async def verify_token(self, token):
            if token != "test-inbound-token":
                return None
            return AccessToken(
                token=token, client_id="test-mcp-client", scopes=[], claims={"sub": "a"}
            )

    class StoreProvider:
        calls = 0

        async def resolve(self):
            self.calls += 1
            token = get_access_token()
            assert token is not None
            account = token.claims["sub"]
            return LightcastCredentials(account, f"secret-{account}")

    provider = StoreProvider()
    app = create_server(provider, auth=TestVerifier()).http_app(
        host_origin_protection=True
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
        ) as raw:
            response = await raw.post(
                "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "server/discover"}
            )
            assert response.status_code == 401
            assert provider.calls == 0
    async with http_server(provider, TestVerifier()) as make_client:
        # The custom provider must choose the authenticated account, ignoring
        # arbitrary account/secret headers supplied by the caller.
        supplied = {**headers("b"), "Authorization": "Bearer test-inbound-token"}
        async with make_client(supplied) as client:
            result = await client.call_tool("get_skill_details", {"skill_id": "KS1"})
            assert result.structured_content["id"] == "a"
    assert provider.calls == 1
    assert upstream == [("oauth", "a", "emsi_open"), ("api", "a", "emsi_open")]


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_credentials_are_read_again_on_each_http_request(
    monkeypatch, upstream, mode
):
    monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "headers")
    app = create_server().http_app(host_origin_protection=True)
    current = headers("a")

    async def set_headers(request):
        for name in ("X-Lightcast-Client-Id", "X-Lightcast-Client-Secret"):
            request.headers.pop(name, None)
        request.headers.update(current)

    def factory(**kwargs):
        return httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            event_hooks={"request": [set_headers]},
            **kwargs,
        )

    async with app.router.lifespan_context(app):
        async with Client(
            StreamableHttpTransport(
                "http://127.0.0.1/mcp", httpx_client_factory=factory
            ),
            mode=mode,
        ) as client:
            for account in ("a", "b", None, "a"):
                current = headers(account) if account else {}
                result = await client.call_tool(
                    "get_skill_details", {"skill_id": "KS1"}, raise_on_error=False
                )
                if account:
                    assert (
                        not result.is_error
                        and result.structured_content["id"] == account
                    )
                else:
                    assert result.is_error
    assert sorted(call for call in upstream if call[0] == "oauth") == [
        ("oauth", "a", "emsi_open"),
        ("oauth", "b", "emsi_open"),
    ]


async def test_upstream_401_refreshes_only_the_affected_account(monkeypatch, upstream):
    monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "headers")
    async with http_server() as make_client:

        async def request(account):
            async with make_client(headers(account)) as client:
                for _ in range(2):
                    result = await client.call_tool(
                        "get_skill_details", {"skill_id": "KS1"}
                    )
                    assert result.structured_content["id"] == account

        await asyncio.gather(request("refresh"), request("b"))
    assert upstream.count(("oauth", "refresh", "emsi_open")) == 2
    assert upstream.count(("oauth", "b", "emsi_open")) == 1
