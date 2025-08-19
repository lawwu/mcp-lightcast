"""Base API client for Lightcast APIs."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import httpx
from pydantic import BaseModel

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import lightcast_config
except ImportError:
    from pydantic_settings import BaseSettings
    from pydantic import Field, ConfigDict
    
    class LightcastConfig(BaseSettings):
        model_config = ConfigDict(extra="ignore")
        
        client_id: str = Field(default="", alias="LIGHTCAST_CLIENT_ID")
        client_secret: str = Field(default="", alias="LIGHTCAST_CLIENT_SECRET")
        base_url: str = Field(default="https://api.lightcast.io", alias="LIGHTCAST_BASE_URL")
    
    lightcast_config = LightcastConfig()

from ..auth.oauth import lightcast_auth, AuthenticationError


class APIError(Exception):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""
    pass


class BaseLightcastClient(ABC):
    """Base client for Lightcast API interactions."""
    
    def __init__(self):
        self.base_url = lightcast_config.base_url
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Lightcast API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Replace version placeholder in URL
        if "{version}" in url:
            url = url.replace("{version}", version)
        
        try:
            headers = await lightcast_auth.get_auth_headers()
            
            # Handle different content types
            if isinstance(data, str):
                headers["Content-Type"] = "text/plain"
                json_data = None
                content = data
            else:
                json_data = data
                content = None
            
            response = await self.client.request(
                method=method,
                url=url,
                json=json_data,
                content=content,
                params=params,
                headers=headers
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                rate_limit_reset = response.headers.get("RateLimit-Reset")
                raise RateLimitError(
                    f"Rate limit exceeded. Reset at: {rate_limit_reset}",
                    status_code=429,
                    response_data={"reset_time": rate_limit_reset}
                )
            
            response.raise_for_status()
            
            # Handle different response types
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                return {"data": response.text, "content_type": content_type}
                
        except httpx.HTTPStatusError as e:
            error_data = None
            try:
                error_data = e.response.json() if e.response.headers.get("content-type", "").startswith("application/json") else {"error": e.response.text}
            except:
                error_data = {"error": str(e)}
            
            raise APIError(
                f"API request failed: {e.response.status_code} {e.response.reason_phrase}",
                status_code=e.response.status_code,
                response_data=error_data
            )
        except AuthenticationError:
            raise
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, version: str = "2023.4") -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params, version=version)
    
    async def post(self, endpoint: str, data: Optional[Union[Dict, str]] = None, params: Optional[Dict[str, Any]] = None, version: str = "2023.4") -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, data=data, params=params, version=version)
    
    async def put(self, endpoint: str, data: Optional[Union[Dict, str]] = None, params: Optional[Dict[str, Any]] = None, version: str = "2023.4") -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request("PUT", endpoint, data=data, params=params, version=version)
    
    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, version: str = "2023.4") -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request("DELETE", endpoint, params=params, version=version)