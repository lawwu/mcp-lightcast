"""Transport resilience without retries that exhaust a quota."""

import httpx
import pytest

from mcp_lightcast.apis.base import (
    APIError,
    BaseLightcastClient,
    RateLimitError,
    segment,
)
from mcp_lightcast.auth.oauth import lightcast_auth


@pytest.mark.parametrize(
    "api,path",
    [
        ("skills", "skills"),
        ("titles", "titles"),
        ("similarity", "similarity"),
        ("job_postings", "jpa"),
        ("occupation_benchmark", "occupation-benchmark"),
        ("career_pathways", "career-pathways"),
    ],
)
async def test_custom_base_url_is_respected(api, path, monkeypatch):
    monkeypatch.setenv("LIGHTCAST_BASE_URL", "https://example.test/api/")
    async with BaseLightcastClient(api) as c:
        assert c.base_url == f"https://example.test/api/{path}"


async def test_scope_override(monkeypatch):
    monkeypatch.setenv("LIGHTCAST_API_SCOPES", '{"classification":"lightcast_open"}')
    async with BaseLightcastClient("classification") as c:
        assert c.required_scope == "lightcast_open"


async def test_short_retry_after_is_honored(api_mock):
    api_mock.add_response(status_code=429, headers={"Retry-After": "0"})
    api_mock.add_response(json={"data": []})
    async with BaseLightcastClient("skills") as c:
        assert await c.get("meta") == {"data": []}
    assert len(api_mock.get_requests()) == 2


@pytest.mark.parametrize(
    "headers", [{"RateLimit-Reset": "9999999999"}, {"Retry-After": "3600"}]
)
async def test_quota_is_not_retried(api_mock, headers):
    api_mock.add_response(status_code=429, headers=headers)
    async with BaseLightcastClient("titles") as c:
        with pytest.raises(RateLimitError) as exc:
            await c.get("meta")
    assert exc.value.status_code == 429
    assert len(api_mock.get_requests()) == 1


async def test_401_refreshes_only_once(api_mock, monkeypatch):
    invalidations = []
    monkeypatch.setattr(
        lightcast_auth, "invalidate", lambda *args, **kwargs: invalidations.append(args)
    )
    api_mock.add_response(status_code=401)
    api_mock.add_response(status_code=401)
    async with BaseLightcastClient("titles") as c:
        with pytest.raises(APIError) as exc:
            await c.get("meta")
    assert exc.value.status_code == 401
    assert len(invalidations) == 1


async def test_non_json_response_fails(api_mock):
    api_mock.add_response(text="not JSON")
    async with BaseLightcastClient("skills") as c:
        with pytest.raises(APIError, match="invalid JSON"):
            await c.get("meta")


async def test_transient_retries_are_bounded(api_mock, monkeypatch):
    monkeypatch.setattr(
        BaseLightcastClient, "_retry_delay", staticmethod(lambda *args: 0)
    )
    for _ in range(3):
        api_mock.add_response(status_code=503)
    async with BaseLightcastClient("skills") as c:
        with pytest.raises(APIError) as exc:
            await c.get("meta")
    assert exc.value.status_code == 503
    assert len(api_mock.get_requests()) == 3


async def test_transport_exception_is_sanitized(api_mock):
    api_mock.add_exception(httpx.ReadTimeout("secret request text"))
    async with BaseLightcastClient("skills") as c:
        with pytest.raises(APIError, match="ReadTimeout") as exc:
            await c.get("meta")
    assert "secret request text" not in str(exc.value)


@pytest.mark.parametrize("value", ["", ".", ".."])
def test_bad_segments(value):
    with pytest.raises(ValueError):
        segment(value)


def test_identifiers_are_url_encoded():
    assert segment("a/b?x=y") == "a%2Fb%3Fx%3Dy"


async def test_cancellation_propagates_without_retry(api_mock, monkeypatch):
    import asyncio

    calls = []
    async with BaseLightcastClient("skills") as client:

        async def cancel(**kwargs):
            calls.append(kwargs)
            raise asyncio.CancelledError()

        monkeypatch.setattr(client.client, "request", cancel)
        with pytest.raises(asyncio.CancelledError):
            await client.get("meta")
    assert len(calls) == 1
