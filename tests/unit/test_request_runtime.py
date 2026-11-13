"""Request ownership is tested through clients, MCP calls, and HTTP adapters."""

import asyncio
import json
from urllib.parse import parse_qs

import httpx
import pytest
from fastmcp import Client

from mcp_lightcast.apis.base import (
    APIError,
    BaseLightcastClient,
    RequestRuntime,
    get_request_runtime,
)
from mcp_lightcast.auth.credentials import (
    LightcastCredentials,
    credential_provider_context,
)
from mcp_lightcast.server import create_server
from mcp_lightcast.settings import get_settings
from mcp_lightcast.utils.version_manager import VersionManager


def token_response(value):
    return httpx.Response(
        200, json={"access_token": value, "token_type": "Bearer", "expires_in": 30}
    )


def tracked_factory(handler, transports):
    class Transport(httpx.MockTransport):
        closed = False

        async def aclose(self):
            self.closed = True
            await super().aclose()

    def factory():
        transport = Transport(handler)
        transports.append(transport)
        return transport

    return factory


async def test_explicit_servers_keep_workflows_health_and_metadata_with_their_owner(
    clock,
):
    versions = VersionManager()

    async def exercise(account):
        calls, transports = [], []
        config = get_settings().model_copy(
            update={
                "base_url": f"https://{account}.example.test",
                "oauth_url": f"https://{account}.example.test/token",
                "client_id": "must-not-use-environment-account",
            }
        )

        class Provider:
            calls = 0

            async def resolve(self):
                self.calls += 1
                await asyncio.sleep(0)
                return LightcastCredentials(account, f"secret-{account}")

        async def respond(request):
            await asyncio.sleep(0)
            assert request.url.host == f"{account}.example.test"
            calls.append(request)
            if request.url.path == "/token":
                assert parse_qs(request.content.decode())["client_id"] == [account]
                return token_response(account)
            assert request.headers["Authorization"] == f"Bearer {account}"
            if request.url.path.endswith("/normalize"):
                return httpx.Response(
                    200, json={"data": {"title": {"id": account}, "confidence": 1}}
                )
            if request.url.path.endswith("/extract"):
                return httpx.Response(
                    200, json={"data": [{"skill": {"id": account}, "confidence": 1}]}
                )
            return httpx.Response(200, json={"data": {"latestVersion": account}})

        provider = Provider()
        runtime = RequestRuntime(
            config, transport_factory=tracked_factory(respond, transports), clock=clock
        )
        async with Client(create_server(provider, runtime=runtime)) as client:
            assert len(await client.list_tools()) == 37
            await client.read_resource("lightcast://server/info")
            assert not calls and provider.calls == 0
            result = await client.call_tool(
                "analyze_job_posting_skills",
                {"job_title": "Python", "job_description": "SQL"},
            )
            assert result.structured_content["combined_skills"][0]["id"] == account
            assert provider.calls == 1
            health = await client.read_resource("lightcast://server/health")
            assert json.loads(health[0].text)["status"] == "healthy"
            assert provider.calls == 2
        with runtime.context(), credential_provider_context(provider):
            assert await versions.get_latest_skills_version() == account
            assert await versions.get_latest_skills_version() == account
        assert sum(request.url.path == "/token" for request in calls) == 1
        assert provider.calls == 3
        assert transports and all(transport.closed for transport in transports)

    original = get_request_runtime()
    await asyncio.gather(exercise("a"), exercise("b"))
    assert get_request_runtime() is original


async def test_requests_refresh_expired_tokens_without_recreating_owner(clock):
    issued, transports = [], []

    def respond(request):
        if request.url.path == "/connect/token":
            issued.append(f"token-{len(issued)}")
            return token_response(issued[-1])
        return httpx.Response(200, json={"token": request.headers["Authorization"]})

    runtime = RequestRuntime(
        transport_factory=tracked_factory(respond, transports), clock=clock
    )
    with runtime.context():
        for expected, advance in (("token-0", 0), ("token-0", 0), ("token-1", 30)):
            clock.now += advance
            async with BaseLightcastClient("skills") as client:
                assert await client.get("meta") == {"token": f"Bearer {expected}"}
    assert len(issued) == 2
    assert all(transport.closed for transport in transports)


async def test_late_401_keeps_the_token_refreshed_by_another_request(clock):
    old_request_started, refreshed = asyncio.Event(), asyncio.Event()
    issued, transports = [], []

    async def respond(request):
        if request.url.path == "/connect/token":
            issued.append(f"token-{len(issued)}")
            return token_response(issued[-1])
        if request.headers["Authorization"] == "Bearer token-0":
            if request.url.path.endswith("/slow"):
                old_request_started.set()
                await refreshed.wait()
            else:
                await old_request_started.wait()
            return httpx.Response(401)
        refreshed.set()
        return httpx.Response(200, json={"token": request.headers["Authorization"]})

    runtime = RequestRuntime(
        transport_factory=tracked_factory(respond, transports), clock=clock
    )

    async def lookup(endpoint):
        with runtime.context():
            async with BaseLightcastClient("skills") as client:
                return await client.get(endpoint)

    results = await asyncio.wait_for(asyncio.gather(lookup("slow"), lookup("fast")), 2)
    assert results == [{"token": "Bearer token-1"}] * 2
    assert len(issued) == 2
    assert all(transport.closed for transport in transports)


async def test_cancellation_releases_rate_wait_and_restores_context(clock):
    waiting, release = asyncio.Event(), asyncio.Event()
    transports, calls = [], []

    class WaitingClock(type(clock)):
        async def sleep(self, seconds):
            if seconds:
                waiting.set()
                await release.wait()
            await super().sleep(seconds)

    waiting_clock = WaitingClock()

    def respond(request):
        if request.url.path == "/connect/token":
            return token_response("token")
        calls.append(request)
        return httpx.Response(200, json={})

    config = get_settings().model_copy(update={"requests_per_second": 1})
    runtime = RequestRuntime(
        config,
        transport_factory=tracked_factory(respond, transports),
        clock=waiting_clock,
    )

    async def lookup():
        previous = get_request_runtime()
        try:
            with runtime.context():
                async with BaseLightcastClient("skills") as client:
                    return await client.get("meta")
        finally:
            assert get_request_runtime() is previous

    await lookup()
    cancelled = asyncio.create_task(lookup())
    await asyncio.wait_for(waiting.wait(), 2)
    following = asyncio.create_task(lookup())
    await asyncio.sleep(0)
    cancelled.cancel()
    with pytest.raises(asyncio.CancelledError):
        await cancelled
    release.set()
    assert await asyncio.wait_for(following, 2) == {}
    assert len(calls) == 2
    assert waiting_clock.delays == [0, 1]
    assert all(transport.closed for transport in transports)


def test_shared_owner_can_be_used_from_successive_event_loops(clock):
    issued, transports = [], []

    def respond(request):
        if request.url.path == "/connect/token":
            issued.append(request)
            return token_response("token")
        return httpx.Response(200, json={})

    runtime = RequestRuntime(
        get_settings().model_copy(update={"requests_per_second": 1}),
        transport_factory=tracked_factory(respond, transports),
        clock=clock,
    )

    async def lookup():
        with runtime.context():
            async with BaseLightcastClient("skills") as client:
                assert await client.get("meta") == {}

    asyncio.run(lookup())
    asyncio.run(lookup())
    assert len(issued) == 1
    assert clock.delays == [0, 0]
    assert all(transport.closed for transport in transports)


@pytest.mark.parametrize("other_scope", ["allowed", "denied"])
async def test_metadata_cache_stays_with_its_runtime_even_for_the_same_account(
    clock, other_scope
):
    versions = VersionManager()
    calls = []

    def runtime(scope, permitted):
        config = get_settings().model_copy(update={"api_scopes": {"skills": scope}})

        def respond(request):
            calls.append((permitted, request.url.path))
            if request.url.path == "/connect/token":
                return token_response(scope)
            return httpx.Response(
                200 if permitted else 403,
                json={"data": {"latestVersion": "allowed-version"}},
            )

        return RequestRuntime(
            config, transport_factory=lambda: httpx.MockTransport(respond), clock=clock
        )

    with runtime("allowed", True).context():
        assert await versions.get_latest_skills_version() == "allowed-version"
        assert await versions.get_latest_skills_version() == "allowed-version"
    with runtime(other_scope, False).context():
        with pytest.raises(APIError, match="403"):
            await versions.get_latest_skills_version()
    assert calls == [
        (True, "/connect/token"),
        (True, "/skills/meta"),
        (False, "/connect/token"),
        (False, "/skills/meta"),
    ]


async def test_metadata_cache_respects_changed_scope_within_one_runtime(clock):
    config = get_settings().model_copy(update={"api_scopes": {"skills": "allowed"}})
    scopes = []

    def respond(request):
        if request.url.path == "/connect/token":
            scope = parse_qs(request.content.decode())["scope"][0]
            scopes.append(scope)
            return token_response(scope)
        permitted = request.headers["Authorization"] == "Bearer allowed"
        return httpx.Response(
            200 if permitted else 403,
            json={"data": {"latestVersion": "allowed-version"}},
        )

    owner = RequestRuntime(
        config, transport_factory=lambda: httpx.MockTransport(respond), clock=clock
    )
    versions = VersionManager()
    with owner.context():
        assert await versions.get_latest_skills_version() == "allowed-version"
        config.api_scopes["skills"] = "denied"
        with pytest.raises(APIError, match="403"):
            await versions.get_latest_skills_version()
    assert scopes == ["allowed", "denied"]


async def test_legacy_auth_import_honors_runtime_request_credentials(clock):
    submitted = []

    class Provider:
        async def resolve(self):
            return LightcastCredentials("request-account", "synthetic-secret")

    def respond(request):
        submitted.append(parse_qs(request.content.decode())["client_id"][0])
        return token_response("request-token")

    runtime = RequestRuntime(
        get_settings().model_copy(update={"client_id": "environment-account"}),
        transport_factory=lambda: httpx.MockTransport(respond),
        clock=clock,
    )
    with runtime.context(), credential_provider_context(Provider()):
        from mcp_lightcast.auth.oauth import lightcast_auth

        assert await lightcast_auth.get_access_token() == "request-token"
        assert await runtime.authenticate() == "request-token"
        assert (await lightcast_auth.get_auth_headers())[
            "Authorization"
        ] == "Bearer request-token"
    assert submitted == ["request-account"]
