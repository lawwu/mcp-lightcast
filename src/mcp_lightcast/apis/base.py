"""Shared transport for documented, read-only Lightcast API operations."""

import asyncio
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Protocol, Self
from urllib.parse import quote
from weakref import WeakKeyDictionary

import httpx
from fastmcp.exceptions import ToolError

from ..auth.credentials import (
    ConfiguredCredentialProvider,
    LightcastCredentials,
    get_credentials,
)
from ..auth.oauth import LightcastAuth
from ..settings import LightcastConfig, get_settings


class APIError(ToolError):
    """Safe, actionable text for MCP; raw response_data stays inside Python."""

    def __init__(
        self, message: str, status_code: int | None = None, response_data: Any = None
    ):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class RateLimitError(APIError):
    """Quota or request rate exceeded; response_data contains reset headers."""


def segment(value: str) -> str:
    """Keep caller-provided IDs within a single URL path segment."""
    if not value or value in {".", ".."}:
        raise ValueError(
            "An identifier or version must be nonempty and cannot be '.' or '..'."
        )
    return quote(value, safe="")


@dataclass
class _RateState:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    next_request: float = 0.0
    users: int = 0


class Clock(Protocol):
    """Time adapter shared by token expiry, rate spacing, and retry delays."""

    def monotonic(self) -> float: ...

    def utcnow(self) -> datetime: ...

    async def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def utcnow(self) -> datetime:
        return datetime.now(UTC)

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class RequestRuntime:
    """Own shared Lightcast request state without keeping HTTP clients open.

    The default runtime is process-shared and loads configuration lazily. An
    explicit runtime isolates configuration and caches; reuse it across clients
    and servers that must share an account's rate budget. Transport factories
    return a fresh adapter for each short-lived HTTP client, including OAuth.
    """

    def __init__(
        self,
        config: LightcastConfig | None = None,
        *,
        transport_factory: Callable[[], httpx.AsyncBaseTransport] | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._config = config
        self._transport_factory = transport_factory
        self._clock = clock if clock is not None else SystemClock()
        self._rate_state: WeakKeyDictionary = WeakKeyDictionary()
        self._auth = LightcastAuth(
            config,
            client_factory=self._new_client,
            monotonic=self._clock.monotonic,
            credential_resolver=self.credentials,
        )

    @property
    def config(self) -> LightcastConfig:
        return self._config if self._config is not None else get_settings()

    def _new_client(self) -> httpx.AsyncClient:
        transport = self._transport_factory() if self._transport_factory else None
        return httpx.AsyncClient(timeout=self.config.timeout, transport=transport)

    async def credentials(self) -> LightcastCredentials:
        return await get_credentials(ConfiguredCredentialProvider(self.config))

    async def authenticate(self) -> str:
        """Check the current caller's default scope using this runtime's cache."""
        return await self._auth.get_access_token()

    @contextmanager
    def context(self) -> Iterator[None]:
        """Select this runtime for an operation and its asynchronous child tasks."""
        token = _request_runtime.set(self)
        try:
            yield
        finally:
            _request_runtime.reset(token)

    async def _throttle(
        self, base_url: str, api_name: str | None, credentials: LightcastCredentials
    ) -> None:
        states = self._rate_state.setdefault(asyncio.get_running_loop(), {})
        key = (
            base_url,
            credentials.identity(self.config.oauth_url, include_secret=False),
        )
        if key not in states:
            for stale_key, state in list(states.items()):
                if state.users == 0 and state.next_request <= self._clock.monotonic():
                    del states[stale_key]
            if len(states) >= 1024:
                raise APIError("Server credential capacity reached; retry later.")
            states[key] = _RateState()
        state = states[key]
        state.users += 1
        try:
            async with state.lock:
                await self._clock.sleep(
                    max(0, state.next_request - self._clock.monotonic())
                )
                rate = (
                    self.config.core_lmi_requests_per_second
                    if api_name == "core_lmi"
                    else self.config.requests_per_second
                )
                state.next_request = self._clock.monotonic() + 1 / rate
        finally:
            state.users -= 1


_default_runtime = RequestRuntime()
_request_runtime: ContextVar[RequestRuntime | None] = ContextVar(
    "lightcast_request_runtime", default=None
)


def get_request_runtime() -> RequestRuntime:
    runtime = _request_runtime.get()
    return runtime if runtime is not None else _default_runtime


class BaseLightcastClient:
    API_SCOPES = {
        "classification": "classification_api",
        "similarity": "similarity",
        "occupation_benchmark": "occupation-benchmark",
        "career_pathways": "career-pathways",
        "job_postings": "postings:us",
        "core_lmi": "agnitio",
    }
    API_PATHS = {
        "skills": "skills",
        "titles": "titles",
        "similarity": "similarity",
        "occupation_benchmark": "occupation-benchmark",
        "career_pathways": "career-pathways",
        "job_postings": "jpa",
    }

    def __init__(self, api_name: str | None = None) -> None:
        self._runtime = get_request_runtime()
        self.config = self._runtime.config
        self.api_name = api_name
        self.base_url = self.config.base_url.rstrip("/")
        if api_name == "classification":
            self.base_url = self.config.classification_url.rstrip("/")
        elif api_name == "core_lmi":
            self.base_url = self.config.core_lmi_url.rstrip("/")
        elif api_name in self.API_PATHS:
            self.base_url += "/" + self.API_PATHS[api_name]
        self.required_scope = self.config.api_scopes.get(
            api_name or "", self.API_SCOPES.get(api_name or "", self.config.oauth_scope)
        )
        self.client = self._runtime._new_client()
        self._auth = self._runtime._auth

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        await self.client.aclose()
        return None

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float | None:
        raw = response.headers.get("Retry-After")
        if raw:
            try:
                delay = float(raw)
            except ValueError:
                try:
                    delay = (
                        parsedate_to_datetime(raw) - self._runtime._clock.utcnow()
                    ).total_seconds()
                except TypeError, ValueError:
                    return None
            return max(0, delay) if delay <= 5 else None
        # A 429 without Retry-After may be a monthly/yearly quota.
        return None if response.status_code == 429 else 0.5 * 2**attempt

    async def _request_json(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: dict[str, Any] | None = None,
        version: str = "latest",
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}".replace(
            "{version}", segment(version)
        )
        refreshed = False
        retries = 0
        credentials = await self._runtime.credentials()
        while True:
            headers = await self._auth.get_auth_headers(
                self.required_scope, credentials=credentials
            )
            if isinstance(data, str):
                headers["Content-Type"] = "text/plain"
            await self._runtime._throttle(self.base_url, self.api_name, credentials)
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=None if isinstance(data, str) else data,
                    content=data if isinstance(data, str) else None,
                )
            except httpx.RequestError as exc:
                raise APIError(
                    f"Lightcast request failed ({type(exc).__name__})."
                ) from None
            if response.status_code == 401 and not refreshed:
                self._auth.invalidate(
                    self.required_scope,
                    headers["Authorization"].removeprefix("Bearer "),
                    credentials=credentials,
                )
                refreshed = True
                continue
            if (
                response.status_code in {429, 502, 503, 504}
                and retries < self.config.max_retries
            ):
                delay = self._retry_delay(response, retries)
                if delay is not None:
                    await self._runtime._clock.sleep(delay)
                    retries += 1
                    continue
            if response.status_code == 429:
                raise RateLimitError(
                    "Lightcast rate limit or quota exceeded. Check reset headers before retrying.",
                    429,
                    {
                        "retry_after": response.headers.get("Retry-After"),
                        "reset_time": response.headers.get("RateLimit-Reset")
                        or response.headers.get("X-Rate-Limit-Reset"),
                        "remaining": response.headers.get("RateLimit-Remaining")
                        or response.headers.get("X-Rate-Limit-Remaining"),
                        "limit": response.headers.get("X-Rate-Limit-Limit"),
                    },
                )
            if not response.is_success:
                try:
                    details = response.json()
                except ValueError:
                    details = None
                hint = (
                    " Check your API scope and subscription permissions."
                    if response.status_code in {401, 403}
                    else ""
                )
                raise APIError(
                    f"Lightcast {self.api_name or 'API'} request failed (HTTP {response.status_code}).{hint}",
                    response.status_code,
                    details,
                )
            try:
                result = response.json()
            except ValueError:
                raise APIError("Lightcast returned an invalid JSON response.") from None
            return result

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: dict[str, Any] | None = None,
        version: str = "latest",
    ) -> dict[str, Any]:
        result = await self._request_json(method, endpoint, data, params, version)
        if not isinstance(result, dict):
            raise APIError("Lightcast returned an unexpected response shape.")
        return result

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        version: str = "latest",
    ) -> dict[str, Any]:
        return await self._make_request("GET", endpoint, params=params, version=version)

    async def post(
        self,
        endpoint: str,
        data: Any = None,
        params: dict[str, Any] | None = None,
        version: str = "latest",
    ) -> dict[str, Any]:
        return await self._make_request(
            "POST", endpoint, data=data, params=params, version=version
        )
