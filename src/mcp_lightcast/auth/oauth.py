"""OAuth2 authentication for Lightcast API."""

import asyncio
import sys
import time
from pathlib import Path

import httpx
from pydantic import BaseModel

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import lightcast_config
except ImportError:
    from pydantic import ConfigDict, Field
    from pydantic_settings import BaseSettings

    class LightcastConfig(BaseSettings):
        model_config = ConfigDict(extra="ignore")

        client_id: str = Field(default="", alias="LIGHTCAST_CLIENT_ID")
        client_secret: str = Field(default="", alias="LIGHTCAST_CLIENT_SECRET")
        oauth_url: str = Field(default="https://auth.emsicloud.com/connect/token", alias="LIGHTCAST_OAUTH_URL")
        oauth_scope: str = Field(default="emsi_open", alias="LIGHTCAST_OAUTH_SCOPE")

    lightcast_config = LightcastConfig()


class TokenResponse(BaseModel):
    """OAuth2 token response model."""
    access_token: str
    token_type: str
    expires_in: int
    scope: str | None = None


class LightcastAuth:
    """OAuth2 authentication handler for Lightcast API."""

    def __init__(self):
        self.client_id = lightcast_config.client_id
        self.client_secret = lightcast_config.client_secret
        self.oauth_url = lightcast_config.oauth_url
        self.oauth_scope = getattr(lightcast_config, 'oauth_scope', 'emsi_open')
        self._scope: str | None = None  # Dynamic scope override
        self._token: str | None = None
        self._token_expires_at: float = 0
        self._lock = asyncio.Lock()
        self._current_scope: str | None = None  # Track which scope the current token was issued for

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        async with self._lock:
            if self._is_token_valid():
                return self._token

            await self._refresh_token()
            return self._token

    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired."""
        if not self._token:
            return False

        # Check if the scope has changed and we need a new token
        current_scope = self._scope or self.oauth_scope
        if self._current_scope != current_scope:
            return False

        # Add 60 second buffer to prevent token expiration during request
        return time.time() < (self._token_expires_at - 60)

    async def _refresh_token(self) -> None:
        """Refresh the OAuth2 access token."""
        # Use the dynamic scope if set, otherwise use the default scope
        current_scope = self._scope or self.oauth_scope

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": current_scope
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.oauth_url,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()

                token_data = TokenResponse(**response.json())
                self._token = token_data.access_token
                self._token_expires_at = time.time() + token_data.expires_in
                self._current_scope = current_scope  # Track which scope this token was issued for

            except httpx.HTTPStatusError as e:
                raise AuthenticationError(f"Failed to get access token: {e.response.status_code} {e.response.text}")
            except Exception as e:
                raise AuthenticationError(f"Authentication error: {str(e)}")

    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
    pass


# Global auth instance
lightcast_auth = LightcastAuth()
