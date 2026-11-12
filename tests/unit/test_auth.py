"""Authentication regressions: scope isolation, expiry, concurrency, and secrecy."""

import asyncio
import time
from urllib.parse import parse_qs

import httpx
import pytest

from mcp_lightcast.auth.credentials import get_credentials
from mcp_lightcast.auth.oauth import AuthenticationError, LightcastAuth


async def test_scopes_are_isolated_and_refresh_once(httpx_mock):
    calls = []

    def respond(request):
        scope = parse_qs(request.content.decode())["scope"][0]
        calls.append(scope)
        return httpx.Response(
            200,
            json={
                "access_token": f"token-{scope}",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )

    httpx_mock.add_callback(respond, is_reusable=True)
    auth = LightcastAuth()
    scopes = [
        "emsi_open",
        "similarity",
        "emsi_open",
        "similarity",
        "classification_api",
    ]
    tokens = await asyncio.gather(*(auth.get_access_token(s) for s in scopes))
    assert tokens == [f"token-{s}" for s in scopes]
    assert sorted(calls) == ["classification_api", "emsi_open", "similarity"]


async def test_expired_token_refresh_and_stale_invalidation(httpx_mock):
    auth = LightcastAuth()
    credentials = await get_credentials()
    key = (credentials.identity(auth.config.oauth_url), "emsi_open")
    auth._tokens[key] = ("old", time.monotonic() - 1)
    httpx_mock.add_response(
        json={"access_token": "new", "token_type": "Bearer", "expires_in": 3600}
    )
    assert await auth.get_access_token() == "new"
    auth.invalidate("emsi_open", "old", credentials=credentials)
    assert await auth.get_access_token() == "new"
    auth.invalidate("emsi_open", "new", credentials=credentials)
    assert key not in auth._tokens


async def test_short_lived_token_is_cached(httpx_mock):
    auth = LightcastAuth()
    httpx_mock.add_response(
        json={"access_token": "short", "token_type": "Bearer", "expires_in": 30}
    )
    assert await auth.get_access_token() == await auth.get_access_token() == "short"


@pytest.mark.parametrize("status", [400, 401, 403, 500])
async def test_auth_errors_never_leak_response_body(httpx_mock, status):
    httpx_mock.add_response(
        status_code=status, text="client_secret=do-not-expose token=secret"
    )
    with pytest.raises(AuthenticationError) as exc:
        await LightcastAuth().get_access_token("similarity")
    assert str(status) in str(exc.value)
    assert "do-not-expose" not in str(exc.value)
    assert "token=secret" not in str(exc.value)


async def test_bad_token_shape_is_sanitized(httpx_mock):
    httpx_mock.add_response(json={"access_token": "do-not-expose"})
    with pytest.raises(AuthenticationError, match="invalid token response"):
        await LightcastAuth().get_access_token()


async def test_missing_credentials(monkeypatch):
    monkeypatch.setenv("LIGHTCAST_CLIENT_SECRET", "")
    with pytest.raises(AuthenticationError, match="LIGHTCAST_CLIENT_SECRET"):
        await LightcastAuth().get_access_token()
