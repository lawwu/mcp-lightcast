"""OAuth client credentials with isolated tokens for each requested scope."""

import asyncio
import time
from weakref import WeakKeyDictionary

import httpx
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, ValidationError

from ..settings import LightcastConfig, get_settings


class AuthenticationError(ToolError):
    """Credentials, scope, or authentication service could not be validated."""


class TokenResponse(BaseModel):
    access_token: str = Field(min_length=1, repr=False)
    token_type: str
    expires_in: int = Field(gt=0)
    scope: str | None = None


class LightcastAuth:
    def __init__(self, config: LightcastConfig | None = None):
        self._config = config
        self._tokens: dict[str, tuple[str, float]] = {}
        self._locks: WeakKeyDictionary = WeakKeyDictionary()

    @property
    def config(self) -> LightcastConfig:
        return self._config or get_settings()

    async def get_access_token(self, scope: str | None = None) -> str:
        scope = scope or self.config.oauth_scope
        locks = self._locks.setdefault(asyncio.get_running_loop(), {})
        async with locks.setdefault(scope, asyncio.Lock()):
            token, expires_at = self._tokens.get(scope, ("", 0))
            if token and time.monotonic() < expires_at:
                return token
            return await self._refresh_token(scope)

    async def _refresh_token(self, scope: str) -> str:
        config = self.config
        if not config.client_id or not config.client_secret:
            raise AuthenticationError(
                "Set LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET."
            )
        try:
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                response = await client.post(
                    config.oauth_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
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
        except (httpx.RequestError, ValidationError, ValueError):
            raise AuthenticationError(
                "Authentication service failed or returned an invalid token response."
            ) from None
        buffer = min(60, data.expires_in * 0.1)
        self._tokens[scope] = (
            data.access_token,
            time.monotonic() + data.expires_in - buffer,
        )
        return data.access_token

    def invalidate(self, scope: str, token: str) -> None:
        """Do not discard a newer token refreshed by a concurrent request."""
        if self._tokens.get(scope, (None,))[0] == token:
            self._tokens.pop(scope, None)

    async def get_auth_headers(self, scope: str | None = None) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {await self.get_access_token(scope)}",
            "Content-Type": "application/json",
        }


lightcast_auth = LightcastAuth()
