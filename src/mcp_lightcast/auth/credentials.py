"""Credential sources and immutable, request-local credential resolution."""

import asyncio
import hashlib
import hmac
import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Protocol

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from ..settings import LightcastConfig, get_settings

_identity_key = secrets.token_bytes(32)


class CredentialError(ToolError):
    """A safe error that never includes submitted credential values."""


@dataclass(frozen=True, slots=True)
class LightcastCredentials:
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.client_id, self.client_secret)
        ):
            raise CredentialError("Lightcast credentials must both be nonempty.")

    def identity(self, issuer: str, *, include_secret: bool = True) -> str:
        """Opaque, process-local cache key; rotation changes token identity only."""
        parts = [issuer, self.client_id]
        if include_secret:
            parts.append(self.client_secret)
        return hmac.new(
            _identity_key, json.dumps(parts).encode(), hashlib.sha256
        ).hexdigest()


class CredentialProvider(Protocol):
    async def resolve(self) -> LightcastCredentials:
        """Resolve credentials authorized for this caller, or raise CredentialError."""
        ...


class EnvironmentCredentialProvider:
    def __init__(self, config: LightcastConfig | None = None) -> None:
        self._config = config

    async def resolve(self) -> LightcastCredentials:
        config = self._config or get_settings()
        if not config.client_id or not config.client_secret:
            raise CredentialError(
                "Set LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET."
            )
        return LightcastCredentials(config.client_id, config.client_secret)


class HeaderCredentialProvider:
    """Explicit HTTP-only mode. Never falls back to environment credentials."""

    async def resolve(self) -> LightcastCredentials:
        try:
            request = get_http_request()
        except RuntimeError:
            raise CredentialError(
                "Header credentials require an HTTP request."
            ) from None
        values = []
        for name in ("x-lightcast-client-id", "x-lightcast-client-secret"):
            entries = request.headers.getlist(name)
            if (
                len(entries) != 1
                or not entries[0].strip()
                or len(entries[0]) > 4096
                or any(ord(char) < 32 or ord(char) == 127 for char in entries[0])
            ):
                raise CredentialError(
                    "Supply one nonempty X-Lightcast-Client-Id and "
                    "X-Lightcast-Client-Secret header."
                )
            values.append(entries[0])
        return LightcastCredentials(*values)


class ConfiguredCredentialProvider:
    async def resolve(self) -> LightcastCredentials:
        provider = (
            HeaderCredentialProvider()
            if get_settings().credential_mode == "headers"
            else EnvironmentCredentialProvider()
        )
        return await provider.resolve()


class _RequestCredentials:
    def __init__(self, provider: CredentialProvider) -> None:
        self.provider = provider
        self.credentials: LightcastCredentials | None = None
        self.lock = asyncio.Lock()

    async def resolve(self) -> LightcastCredentials:
        async with self.lock:
            if self.credentials is None:
                try:
                    credentials = await self.provider.resolve()
                    if not isinstance(credentials, LightcastCredentials):
                        raise TypeError("Invalid provider result")
                except CredentialError:
                    raise
                except Exception:
                    # Secret-store exceptions can contain URLs, tokens or credentials.
                    raise CredentialError(
                        "Unable to resolve Lightcast credentials."
                    ) from None
                self.credentials = credentials
            return self.credentials


_request_credentials: ContextVar[_RequestCredentials | None] = ContextVar(
    "lightcast_request_credentials", default=None
)


@contextmanager
def credential_provider_context(provider: CredentialProvider) -> Iterator[None]:
    """Bind a provider for one operation, including all of its child API calls."""
    token = _request_credentials.set(_RequestCredentials(provider))
    try:
        yield
    finally:
        _request_credentials.reset(token)


async def get_credentials() -> LightcastCredentials:
    resolver = _request_credentials.get()
    if resolver is None:
        resolver = _RequestCredentials(ConfiguredCredentialProvider())
    return await resolver.resolve()


class CredentialMiddleware(Middleware):
    def __init__(self, provider: CredentialProvider | None = None) -> None:
        self.provider = (
            provider if provider is not None else ConfiguredCredentialProvider()
        )

    async def on_request(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        # Resolve lazily: discovery, server info and HTTP liveness need no secrets.
        # A new context for every request also covers the legacy HTTP transport.
        with credential_provider_context(self.provider):
            return await call_next(context)
