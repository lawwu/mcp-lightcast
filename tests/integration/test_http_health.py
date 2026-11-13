"""Operational probes stay cheap, non-sensitive, and separate from OAuth checks."""

import httpx
import pytest

from mcp_lightcast.apis.base import RequestRuntime
from mcp_lightcast.server import create_server, mcp


@pytest.mark.parametrize("method", ["GET", "HEAD"])
async def test_health_without_credentials_or_upstream_access(method, monkeypatch):
    monkeypatch.delenv("LIGHTCAST_CLIENT_ID", raising=False)
    monkeypatch.delenv("LIGHTCAST_CLIENT_SECRET", raising=False)

    def reject_upstream(request):
        pytest.fail("Probe must not authenticate or contact Lightcast")

    runtime = RequestRuntime(
        transport_factory=lambda: httpx.MockTransport(reject_upstream)
    )
    server = create_server(runtime=runtime)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=server.http_app(host_origin_protection=True)),
        base_url="http://127.0.0.1",
    ) as client:
        response = await client.request(method, "/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["cache-control"] == "no-store"
    if method == "HEAD":
        assert response.content == b""
    else:
        assert response.json() == {"status": "ok"}


async def test_health_rejects_writes():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=mcp.http_app(host_origin_protection=True)),
        base_url="http://127.0.0.1",
    ) as client:
        response = await client.post("/health", json={"status": "pretend-healthy"})
    assert response.status_code == 405
    assert set(response.headers["allow"].split(", ")) == {"GET", "HEAD"}


@pytest.mark.parametrize(
    "headers,status",
    [({"Host": "untrusted.example"}, 421), ({"Origin": "null"}, 403)],
)
async def test_health_keeps_host_and_origin_protection(headers, status):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=mcp.http_app(host_origin_protection=True)),
        base_url="http://127.0.0.1",
    ) as client:
        response = await client.get("/health", headers=headers)
    assert response.status_code == status
