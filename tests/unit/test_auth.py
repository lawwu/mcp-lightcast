"""Unit tests for OAuth authentication module."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.mcp_lightcast.auth.oauth import (
    AuthenticationError,
    LightcastAuth,
    TokenResponse,
)


class TestLightcastAuth:
    """Test cases for LightcastAuth class."""

    @pytest.fixture
    def auth_instance(self):
        """Create a LightcastAuth instance for testing."""
        with patch('src.mcp_lightcast.auth.oauth.lightcast_config') as mock_config:
            mock_config.client_id = "test_client_id"
            mock_config.client_secret = "test_client_secret"
            mock_config.oauth_url = "https://auth.lightcast.io/oauth/token"
            mock_config.oauth_scope = "emsi_open"
            return LightcastAuth()

    @pytest.mark.asyncio
    async def test_token_response_model(self):
        """Test TokenResponse model validation."""
        token_data = {
            "access_token": "test_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "openapi"
        }

        token = TokenResponse(**token_data)
        assert token.access_token == "test_token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.scope == "openapi"

    def test_is_token_valid_no_token(self, auth_instance):
        """Test token validation when no token exists."""
        assert not auth_instance._is_token_valid()

    def test_is_token_valid_expired_token(self, auth_instance):
        """Test token validation with expired token."""
        auth_instance._token = "test_token"
        auth_instance._token_expires_at = time.time() - 100  # Expired
        assert not auth_instance._is_token_valid()

    def test_is_token_valid_good_token(self, auth_instance):
        """Test token validation with valid token."""
        auth_instance._token = "test_token"
        auth_instance._token_expires_at = time.time() + 3600  # Valid for 1 hour
        auth_instance._current_scope = auth_instance.oauth_scope  # Set current scope
        assert auth_instance._is_token_valid()

    def test_is_token_valid_near_expiry(self, auth_instance):
        """Test token validation near expiry (within 60 second buffer)."""
        auth_instance._token = "test_token"
        auth_instance._token_expires_at = time.time() + 30  # Expires in 30 seconds
        assert not auth_instance._is_token_valid()  # Should be invalid due to 60s buffer

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_instance, mock_successful_response):
        """Test successful token refresh."""
        token_response_data = {
            "access_token": "new_test_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }

        mock_response = mock_successful_response(token_response_data)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            await auth_instance._refresh_token()

            assert auth_instance._token == "new_test_token"
            assert auth_instance._token_expires_at > time.time()

            # Verify the request was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args

            assert call_args[0][0] == "https://auth.lightcast.io/oauth/token"
            assert call_args[1]["data"]["grant_type"] == "client_credentials"
            assert call_args[1]["data"]["client_id"] == "test_client_id"
            assert call_args[1]["data"]["client_secret"] == "test_client_secret"
            assert call_args[1]["data"]["scope"] == "emsi_open"

    @pytest.mark.asyncio
    async def test_refresh_token_http_error(self, auth_instance, mock_error_response):
        """Test token refresh with HTTP error."""
        mock_response = mock_error_response(400, "Invalid client credentials")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_instance._refresh_token()

            assert "Failed to get access token: 400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_network_error(self, auth_instance):
        """Test token refresh with network error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.RequestError("Network error")

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_instance._refresh_token()

            assert "Authentication error: Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_access_token_valid_cached(self, auth_instance):
        """Test getting access token when cached token is valid."""
        auth_instance._token = "cached_token"
        auth_instance._token_expires_at = time.time() + 3600
        auth_instance._current_scope = auth_instance.oauth_scope  # Set current scope

        token = await auth_instance.get_access_token()
        assert token == "cached_token"

    @pytest.mark.asyncio
    async def test_get_access_token_refresh_needed(self, auth_instance, mock_successful_response):
        """Test getting access token when refresh is needed."""
        auth_instance._token = None

        token_response_data = {
            "access_token": "refreshed_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }

        mock_response = mock_successful_response(token_response_data)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            token = await auth_instance.get_access_token()
            assert token == "refreshed_token"

    @pytest.mark.asyncio
    async def test_get_auth_headers(self, auth_instance, mock_successful_response):
        """Test getting authentication headers."""
        token_response_data = {
            "access_token": "test_auth_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }

        mock_response = mock_successful_response(token_response_data)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            headers = await auth_instance.get_auth_headers()

            expected_headers = {
                "Authorization": "Bearer test_auth_token",
                "Content-Type": "application/json"
            }

            assert headers == expected_headers

    @pytest.mark.asyncio
    async def test_concurrent_token_refresh(self, auth_instance, mock_successful_response):
        """Test that concurrent requests for tokens don't cause multiple refreshes."""
        token_response_data = {
            "access_token": "concurrent_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }

        mock_response = mock_successful_response(token_response_data)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            # Make multiple concurrent requests
            import asyncio
            tasks = [auth_instance.get_access_token() for _ in range(5)]
            tokens = await asyncio.gather(*tasks)

            # All should return the same token
            assert all(token == "concurrent_token" for token in tokens)

            # Should only make one HTTP request due to locking
            assert mock_client.post.call_count == 1
