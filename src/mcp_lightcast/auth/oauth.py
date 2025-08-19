"""OAuth2 authentication for Lightcast API."""

import asyncio
import time
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel
from config.settings import lightcast_config


class TokenResponse(BaseModel):
    """OAuth2 token response model."""
    access_token: str
    token_type: str
    expires_in: int
    scope: Optional[str] = None


class LightcastAuth:
    """OAuth2 authentication handler for Lightcast API."""
    
    def __init__(self):
        self.client_id = lightcast_config.client_id
        self.client_secret = lightcast_config.client_secret
        self.oauth_url = lightcast_config.oauth_url
        self._token: Optional[str] = None
        self._token_expires_at: float = 0
        self._lock = asyncio.Lock()
    
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
        
        # Add 60 second buffer to prevent token expiration during request
        return time.time() < (self._token_expires_at - 60)
    
    async def _refresh_token(self) -> None:
        """Refresh the OAuth2 access token."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openapi"
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
                
            except httpx.HTTPStatusError as e:
                raise AuthenticationError(f"Failed to get access token: {e.response.status_code} {e.response.text}")
            except Exception as e:
                raise AuthenticationError(f"Authentication error: {str(e)}")
    
    async def get_auth_headers(self) -> Dict[str, str]:
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