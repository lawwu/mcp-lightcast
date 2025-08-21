"""Base API client for Lightcast APIs."""

import sys
from abc import ABC
from pathlib import Path
from typing import Any

import httpx

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
        base_url: str = Field(default="https://api.lightcast.io", alias="LIGHTCAST_BASE_URL")
        oauth_url: str = Field(default="https://auth.emsicloud.com/connect/token", alias="LIGHTCAST_OAUTH_URL")
        oauth_scope: str = Field(default="emsi_open", alias="LIGHTCAST_OAUTH_SCOPE")

    lightcast_config = LightcastConfig()

from ..auth.oauth import AuthenticationError, lightcast_auth


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""
    pass


class BaseLightcastClient(ABC):
    """Base client for Lightcast API interactions."""

    # API-specific OAuth scopes for premium APIs
    API_SCOPES = {
        "skills": "emsi_open",
        "titles": "emsi_open",
        "classification": "classification_api",  # Still need to confirm this one
        "similarity": "similarity",
        "occupation_benchmark": "occupation-benchmark",
        "career_pathways": "career-pathways",
        "job_postings": "postings:us"
    }

    # Correct base URLs for different APIs based on reference implementation
    API_BASE_URLS = {
        "skills": "https://emsiservices.com/skills",
        "titles": "https://emsiservices.com/titles",
        "classification": "https://classification.emsicloud.com",
        "similarity": "https://emsiservices.com/similarity",
        "occupation_benchmark": "https://emsiservices.com/occupation-benchmark",
        "career_pathways": "https://emsiservices.com/career-pathways",
        "job_postings": "https://emsiservices.com/jpa"
    }

    def __init__(self, api_name: str | None = None):
        # Use API-specific base URL if available, otherwise fall back to default
        if api_name and api_name in self.API_BASE_URLS:
            self.base_url = self.API_BASE_URLS[api_name]
        else:
            self.base_url = lightcast_config.base_url
        self.api_name = api_name

        # Store the required scope for this API client, but don't set it globally yet
        if api_name and api_name in self.API_SCOPES:
            self.required_scope = self.API_SCOPES[api_name]
        else:
            self.required_scope = lightcast_config.oauth_scope

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
        data: dict | str | None = None,
        params: dict[str, Any] | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """Make an authenticated request to the Lightcast API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Replace version placeholder in URL
        if "{version}" in url:
            url = url.replace("{version}", version)

        try:
            # Set the correct scope for this API before getting auth headers
            lightcast_auth._scope = self.required_scope
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
            except Exception:
                error_data = {"error": str(e)}

            raise APIError(
                f"API request failed: {e.response.status_code} {e.response.reason_phrase}",
                status_code=e.response.status_code,
                response_data=error_data
            ) from e
        except AuthenticationError:
            raise
        except RateLimitError:
            raise
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}") from e

    async def get(self, endpoint: str, params: dict[str, Any] | None = None, version: str = "2023.4") -> dict[str, Any]:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params, version=version)

    async def post(self, endpoint: str, data: dict | str | None = None, params: dict[str, Any] | None = None, version: str = "2023.4") -> dict[str, Any]:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, data=data, params=params, version=version)

    async def put(self, endpoint: str, data: dict | str | None = None, params: dict[str, Any] | None = None, version: str = "2023.4") -> dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request("PUT", endpoint, data=data, params=params, version=version)

    async def delete(self, endpoint: str, params: dict[str, Any] | None = None, version: str = "2023.4") -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request("DELETE", endpoint, params=params, version=version)
