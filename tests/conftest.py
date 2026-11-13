"""Offline by default: no local credentials and no accidental network requests."""

import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs

import httpx
import httpx2
import pytest

from mcp_lightcast.apis.base import RequestRuntime
from mcp_lightcast.settings import get_settings


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        help="Allow live Lightcast metadata tests using local credentials.",
    )
    parser.addoption(
        "--proxy",
        action="store_true",
        help="Run Docker/nginx tests using loopback HTTPS and synthetic upstream data.",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--proxy"):
        for item in items:
            if "proxy" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Use --proxy with Docker"))
    if not config.getoption("--live"):
        for item in items:
            if "live" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Use --live to call the actual API.")
                )


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, request):
    get_settings.cache_clear()
    if "live" not in request.node.keywords:
        monkeypatch.setenv("LIGHTCAST_CLIENT_ID", "unit-test-client")
        monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "environment")
        monkeypatch.setenv("LIGHTCAST_CLIENT_SECRET", "unit-test-secret")
        monkeypatch.setenv("LIGHTCAST_BASE_URL", "https://api.lightcast.io")
        monkeypatch.setenv(
            "LIGHTCAST_CLASSIFICATION_URL", "https://classification.emsicloud.com"
        )
        monkeypatch.setenv(
            "LIGHTCAST_OAUTH_URL", "https://auth.emsicloud.com/connect/token"
        )
        monkeypatch.setenv("LIGHTCAST_OAUTH_SCOPE", "emsi_open")
        monkeypatch.setenv("LIGHTCAST_API_SCOPES", "{}")
        monkeypatch.setenv("LIGHTCAST_REQUESTS_PER_SECOND", "100000")
        monkeypatch.setenv("LIGHTCAST_CORE_LMI_URL", "https://agnitio.emsicloud.com")
        monkeypatch.setenv("LIGHTCAST_CORE_LMI_REQUESTS_PER_SECOND", "100000")

        def guarded_transport(original):
            async def guarded(self, http_request):
                if (
                    "proxy" in request.node.keywords
                    and request.config.getoption("--proxy")
                    and http_request.url.host == "127.0.0.1"
                ):
                    return await original(self, http_request)
                raise AssertionError("Unmocked network request in an offline test")

            return guarded

        # Lightcast uses httpx; the MCP SDK uses httpx2. Only the explicit proxy
        # tests may connect over loopback. All external requests remain blocked.
        for library in (httpx, httpx2):
            monkeypatch.setattr(
                library.AsyncHTTPTransport,
                "handle_async_request",
                guarded_transport(library.AsyncHTTPTransport.handle_async_request),
            )
    with RequestRuntime().context():
        yield
    get_settings.cache_clear()


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.delays = []

    def monotonic(self):
        return self.now

    def utcnow(self):
        return datetime(2026, 11, 12, tzinfo=UTC) + timedelta(seconds=self.now)

    async def sleep(self, seconds):
        self.delays.append(seconds)
        self.now += seconds
        await asyncio.sleep(0)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def api_mock(httpx_mock, clock):
    """Real OAuth/cache behavior; endpoint replies still use pytest-httpx.

    Keep synthetic token traffic out of endpoint contract request assertions.
    The delegate is intercepted by pytest-httpx and the offline network guard.
    """
    issued = []

    class AuthenticatedTransport(httpx.AsyncBaseTransport):
        def __init__(self):
            self.delegate = httpx.AsyncHTTPTransport()

        async def handle_async_request(self, request):
            if str(request.url) == get_settings().oauth_url:
                scope = parse_qs(request.content.decode())["scope"][0]
                issued.append(scope)
                return httpx.Response(
                    200,
                    json={
                        "access_token": f"test-{scope}-{len(issued)}",
                        "token_type": "Bearer",
                        "expires_in": 3600,
                    },
                )
            return await self.delegate.handle_async_request(request)

        async def aclose(self):
            await self.delegate.aclose()

    with RequestRuntime(
        transport_factory=AuthenticatedTransport, clock=clock
    ).context():
        yield httpx_mock
