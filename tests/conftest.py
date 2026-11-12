"""Offline by default: no local credentials and no accidental network requests."""

import httpx
import pytest

from mcp_lightcast.auth.oauth import lightcast_auth
from mcp_lightcast.settings import get_settings


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        help="Allow live Lightcast metadata tests using local credentials.",
    )


def pytest_collection_modifyitems(config, items):
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

        async def deny_network(*args, **kwargs):
            raise AssertionError("Unmocked network request in an offline test")

        monkeypatch.setattr(
            httpx.AsyncHTTPTransport, "handle_async_request", deny_network
        )
    yield
    get_settings.cache_clear()
    lightcast_auth._tokens.clear()


@pytest.fixture
def api_mock(httpx_mock, monkeypatch):
    async def headers(scope=None):
        return {
            "Authorization": f"Bearer test-{scope}",
            "Content-Type": "application/json",
        }

    monkeypatch.setattr(lightcast_auth, "get_auth_headers", headers)
    return httpx_mock
