"""Offline by default: no local credentials and no accidental network requests."""

import httpx
import httpx2
import pytest

from mcp_lightcast.auth.oauth import lightcast_auth
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
    lightcast_auth._tokens.clear()
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
    yield
    get_settings.cache_clear()
    lightcast_auth._tokens.clear()


@pytest.fixture
def api_mock(httpx_mock, monkeypatch):
    async def headers(scope=None, *, credentials=None):
        return {
            "Authorization": f"Bearer test-{scope}",
            "Content-Type": "application/json",
        }

    monkeypatch.setattr(lightcast_auth, "get_auth_headers", headers)
    return httpx_mock
