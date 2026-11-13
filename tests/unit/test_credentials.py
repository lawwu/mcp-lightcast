"""Credential sources, rotation, refresh isolation and request context cleanup."""

import asyncio
from dataclasses import FrozenInstanceError
from urllib.parse import parse_qs

import httpx
import pytest
from starlette.requests import Request

from mcp_lightcast.apis.base import BaseLightcastClient
from mcp_lightcast.auth.credentials import (
    CredentialError,
    LightcastCredentials,
    credential_provider_context,
    get_credentials,
)
from mcp_lightcast.auth.oauth import AuthenticationError, LightcastAuth
from mcp_lightcast.settings import get_settings
from mcp_lightcast.utils.version_manager import VersionManager


class FixedProvider:
    def __init__(self, client_id="account-a", secret="secret-a"):
        self.credentials = LightcastCredentials(client_id, secret)
        self.calls = 0

    async def resolve(self):
        self.calls += 1
        await asyncio.sleep(0)
        return self.credentials


def test_credentials_are_immutable_and_repr_is_redacted():
    credentials = LightcastCredentials("private-id", "private-secret")
    assert "private" not in repr(credentials)
    assert "private" not in credentials.identity("issuer")
    with pytest.raises(FrozenInstanceError):
        credentials.client_secret = "changed"


async def test_environment_mode_ignores_request_headers(monkeypatch):
    monkeypatch.setattr(
        "mcp_lightcast.auth.credentials.get_http_request",
        lambda: pytest.fail("Environment mode must not read HTTP credentials"),
    )
    credentials = await get_credentials()
    assert credentials.client_id == "unit-test-client"


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [(b"x-lightcast-client-id", b"account")],
        [(b"x-lightcast-client-id", b"account"), (b"x-lightcast-client-secret", b" ")],
        [
            (b"x-lightcast-client-id", b"account"),
            (b"x-lightcast-client-secret", b"a"),
            (b"x-lightcast-client-secret", b"b"),
        ],
        [
            (b"x-lightcast-client-id", b"a"),
            (b"x-lightcast-client-id", b"b"),
            (b"x-lightcast-client-secret", b"secret"),
        ],
        [
            (b"x-lightcast-client-id", b"account"),
            (b"x-lightcast-client-secret", b"s" * 4097),
        ],
        [
            (b"x-lightcast-client-id", b"account"),
            (b"x-lightcast-client-secret", b"bad\r\nvalue"),
        ],
    ],
)
async def test_invalid_headers_never_fall_back_to_environment(monkeypatch, headers):
    monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "headers")
    monkeypatch.setattr(
        "mcp_lightcast.auth.credentials.get_http_request",
        lambda: Request({"type": "http", "headers": headers}),
    )
    with pytest.raises(CredentialError, match="Supply one nonempty"):
        await get_credentials()


async def test_header_mode_without_http_fails_closed(monkeypatch):
    monkeypatch.setenv("LIGHTCAST_CREDENTIAL_MODE", "headers")
    with pytest.raises(CredentialError, match="require an HTTP request"):
        await get_credentials()


async def test_concurrent_resolution_and_cancellation_reset_context():
    a, b = FixedProvider(), FixedProvider("account-b", "secret-b")

    async def request(provider):
        with credential_provider_context(provider):
            values = await asyncio.gather(*(get_credentials() for _ in range(5)))
            assert all(value is provider.credentials for value in values)
            raise asyncio.CancelledError()

    results = await asyncio.gather(request(a), request(b), return_exceptions=True)
    assert all(isinstance(value, asyncio.CancelledError) for value in results)
    assert a.calls == b.calls == 1
    assert (await get_credentials()).client_id == "unit-test-client"


async def test_provider_exceptions_are_sanitized():
    class BrokenProvider:
        async def resolve(self):
            raise RuntimeError("secret-store-url-with-private-token")

    with credential_provider_context(BrokenProvider()):
        with pytest.raises(CredentialError) as exc:
            await get_credentials()
    assert str(exc.value) == "Unable to resolve Lightcast credentials."


async def test_tokens_isolate_accounts_scopes_secrets_and_issuers(httpx_mock):
    auth = LightcastAuth()
    calls = []

    async def token(request):
        data = parse_qs(request.content.decode())
        key = (
            data["client_id"][0],
            data["client_secret"][0],
            data["scope"][0],
            str(request.url),
        )
        calls.append(key)
        await asyncio.sleep(0)
        if key[1] == "wrong-secret":
            return httpx.Response(401, text="wrong-secret must never leak")
        return httpx.Response(
            200,
            json={
                "access_token": f"token-{len(calls)}-{key[0]}-{key[2]}",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )

    httpx_mock.add_callback(token, is_reusable=True)
    a = LightcastCredentials("a", "secret-a")
    b = LightcastCredentials("b", "secret-b")
    requests = [(a, "emsi_open"), (b, "emsi_open"), (a, "agnitio"), (a, "emsi_open")]
    tokens = await asyncio.gather(
        *(auth.get_access_token(scope, credentials=c) for c, scope in requests)
    )
    assert len(calls) == 3
    assert tokens[0] == tokens[3]
    assert len(set(tokens)) == 3
    with pytest.raises(AuthenticationError) as exc:
        await auth.get_access_token(
            "emsi_open", credentials=LightcastCredentials("a", "wrong-secret")
        )
    assert "wrong-secret" not in str(exc.value)
    assert await auth.get_access_token("emsi_open", credentials=a) == tokens[0]
    rotated = LightcastCredentials("a", "secret-a-v2")
    assert await auth.get_access_token("emsi_open", credentials=rotated) != tokens[0]
    auth.invalidate("emsi_open", tokens[0], credentials=b)
    assert await auth.get_access_token("emsi_open", credentials=b) == tokens[1]
    auth.invalidate("emsi_open", tokens[0], credentials=a)
    assert await auth.get_access_token("emsi_open", credentials=a) != tokens[0]
    get_settings().oauth_url = "https://different-issuer.test/token"
    await auth.get_access_token("emsi_open", credentials=a)
    assert calls[-1][3] == "https://different-issuer.test/token"


async def test_token_cache_is_bounded_and_eviction_reauthenticates(httpx_mock):
    httpx_mock.add_response(
        json={"access_token": "token", "token_type": "Bearer", "expires_in": 3600},
        is_reusable=True,
    )
    auth = LightcastAuth()
    auth.max_cached_tokens = 2
    for name in ("a", "b", "c", "a"):
        await auth.get_access_token(credentials=LightcastCredentials(name, "synthetic"))
    assert len(httpx_mock.get_requests()) == 4


async def test_rate_spacing_is_per_account_and_shared_across_rotations(
    monkeypatch, api_mock, clock
):
    monkeypatch.setenv("LIGHTCAST_REQUESTS_PER_SECOND", "1")
    api_mock.add_response(json={"data": []}, is_reusable=True)
    for provider in (
        FixedProvider("a", "old"),
        FixedProvider("b", "other"),
        FixedProvider("a", "new"),
    ):
        with credential_provider_context(provider):
            async with BaseLightcastClient("skills") as client:
                await client.get("meta")
    assert clock.delays == [0, 0, 1]
    assert len(api_mock.get_requests()) == 3


async def test_metadata_cache_does_not_cross_credentials(api_mock):
    versions = VersionManager()
    api_mock.add_response(json={"data": {"latestVersion": "a-version"}})
    api_mock.add_response(json={"data": {"latestVersion": "b-version"}})
    api_mock.add_response(status_code=403)
    with credential_provider_context(FixedProvider("a", "first")):
        assert await versions.get_latest_skills_version() == "a-version"
        assert await versions.get_latest_skills_version() == "a-version"
    with credential_provider_context(FixedProvider("b", "second")):
        assert await versions.get_latest_skills_version() == "b-version"
    with credential_provider_context(FixedProvider("a", "rotated")):
        from mcp_lightcast.apis.base import APIError

        with pytest.raises(APIError, match="403"):
            await versions.get_latest_skills_version()
