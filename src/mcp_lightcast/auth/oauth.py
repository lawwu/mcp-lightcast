"""OAuth client credentials with isolated tokens for each requested scope."""

import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from weakref import WeakKeyDictionary, WeakValueDictionary

import httpx
from pydantic import BaseModel, Field, ValidationError

from ..settings import LightcastConfig, get_settings
from .credentials import (
    CredentialError,
    EnvironmentCredentialProvider,
    LightcastCredentials,
    get_credentials,
)


class AuthenticationError(CredentialError):
    """Credentials, scope, or authentication service could not be validated."""


class TokenResponse(BaseModel):
    access_token: str = Field(min_length=1, repr=False)
    token_type: str
    expires_in: int = Field(gt=0)
    scope: str | None = None


class LightcastAuth:
    def __init__(
        self,
        config: LightcastConfig | None = None,
        *,
        client_factory: Callable[[], httpx.AsyncClient] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        credential_resolver: Callable[[], Awaitable[LightcastCredentials]]
        | None = None,
    ):
        self._config = config
        self._client_factory = client_factory or (
            lambda: httpx.AsyncClient(timeout=self.config.timeout)
        )
        self._monotonic = monotonic
        self._credential_resolver = credential_resolver
        self._tokens: OrderedDict[tuple[str, str], tuple[str, float]] = OrderedDict()
        self._locks: WeakKeyDictionary = WeakKeyDictionary()
        self.max_cached_tokens = 1024

    @property
    def config(self) -> LightcastConfig:
        return self._config or get_settings()

    async def get_access_token(
        self,
        scope: str | None = None,
        *,
        credentials: LightcastCredentials | None = None,
    ) -> str:
        scope = scope or self.config.oauth_scope
        if credentials is None:
            try:
                if self._credential_resolver is not None:
                    credentials = await self._credential_resolver()
                elif self._config is not None:
                    credentials = await EnvironmentCredentialProvider(
                        self._config
                    ).resolve()
                else:
                    credentials = await get_credentials()
            except CredentialError as exc:
                raise AuthenticationError(str(exc)) from None
        key = (credentials.identity(self.config.oauth_url), scope)
        locks = self._locks.setdefault(
            asyncio.get_running_loop(), WeakValueDictionary()
        )
        # Keep a strong reference while waiting so concurrent refreshes coalesce.
        lock = locks.setdefault(key, asyncio.Lock())
        async with lock:
            token, expires_at = self._tokens.get(key, ("", 0))
            if token and self._monotonic() < expires_at:
                self._tokens.move_to_end(key)
                return token
            return await self._refresh_token(scope, credentials, key)

    async def _refresh_token(
        self, scope: str, credentials: LightcastCredentials, key: tuple[str, str]
    ) -> str:
        config = self.config
        try:
            async with self._client_factory() as client:
                response = await client.post(
                    config.oauth_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": credentials.client_id,
                        "client_secret": credentials.client_secret,
                        "scope": scope,
                    },
                )
                response.raise_for_status()
                data = TokenResponse.model_validate(response.json())
        except httpx.HTTPStatusError as exc:
            raise AuthenticationError(
                f"Authentication failed (HTTP {exc.response.status_code}) for scope '{scope}'. "
                "Check credentials and the scopes enabled for your account."
            ) from None
        except httpx.RequestError, ValidationError, ValueError:
            raise AuthenticationError(
                "Authentication service failed or returned an invalid token response."
            ) from None
        buffer = min(60, data.expires_in * 0.1)
        for expired_key, (_, expiry) in list(self._tokens.items()):
            if expiry <= self._monotonic():
                self._tokens.pop(expired_key, None)
        self._tokens[key] = (
            data.access_token,
            self._monotonic() + data.expires_in - buffer,
        )
        self._tokens.move_to_end(key)
        while len(self._tokens) > self.max_cached_tokens:
            self._tokens.popitem(last=False)
        return data.access_token

    def invalidate(
        self, scope: str, token: str, *, credentials: LightcastCredentials
    ) -> None:
        """Do not discard a newer token refreshed by a concurrent request."""
        key = (credentials.identity(self.config.oauth_url), scope)
        if self._tokens.get(key, (None,))[0] == token:
            self._tokens.pop(key, None)

    async def get_auth_headers(
        self,
        scope: str | None = None,
        *,
        credentials: LightcastCredentials | None = None,
    ) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {await self.get_access_token(scope, credentials=credentials)}",
            "Content-Type": "application/json",
        }


def __getattr__(name: str) -> LightcastAuth:
    # Preserve the historical import without creating a second token owner.
    if name == "lightcast_auth":
        from ..apis.base import get_request_runtime

        return get_request_runtime()._auth
    raise AttributeError(name)
