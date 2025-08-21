"""Unit tests for Titles API client."""

from unittest.mock import AsyncMock, patch

import pytest

from src.mcp_lightcast.apis.base import APIError
from src.mcp_lightcast.apis.titles import (
    TitleDetail,
    TitleNormalizationResult,
    TitlesAPIClient,
    TitleSearchResult,
)


class TestTitlesAPIClient:
    """Test cases for TitlesAPIClient."""

    @pytest.mark.asyncio
    async def test_search_titles_success(self, mock_successful_response, sample_title_search_response):
        """Test successful title search."""
        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_search_response)

            results = await client.search_titles("software engineer", limit=5)

            assert len(results) == 2
            assert isinstance(results[0], TitleSearchResult)
            assert results[0].id == "1"
            assert results[0].name == "Software Engineer"
            assert results[0].type == "Tech"

            # Verify the request was made correctly
            client.client.request.assert_called_once()
            call_args = client.client.request.call_args
            assert "q=software+engineer" in str(call_args) or call_args[1]["params"]["q"] == "software engineer"
            assert call_args[1]["params"]["limit"] == 5

    @pytest.mark.asyncio
    async def test_get_title_by_id_success(self, mock_successful_response):
        """Test successful title detail retrieval."""
        title_detail_response = {
            "data": {
                "id": "123",
                "name": "Software Engineer",
                "type": "Tech",
                "parent": {"id": "100", "name": "Engineering"},
                "children": [{"id": "124", "name": "Senior Software Engineer"}]
            }
        }

        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(title_detail_response)

            result = await client.get_title_by_id("123")

            assert isinstance(result, TitleDetail)
            assert result.id == "123"
            assert result.name == "Software Engineer"
            assert result.parent is not None
            assert result.children is not None
            assert len(result.children) == 1

    @pytest.mark.asyncio
    async def test_normalize_title_success(self, mock_successful_response, sample_title_normalize_response):
        """Test successful title normalization."""
        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_normalize_response)

            result = await client.normalize_title("sr software dev")

            assert isinstance(result, dict)
            assert result["data"]["id"] == "123"
            assert result["data"]["name"] == "Software Engineer"
            assert result["data"]["confidence"] == 0.95

            # Verify the request was made correctly
            client.client.request.assert_called_once()
            call_args = client.client.request.call_args
            # The actual API call uses JSON data with "term" field
            assert call_args[1]["json"]["term"] == "sr software dev"

    @pytest.mark.asyncio
    async def test_get_title_hierarchy_success(self, mock_successful_response):
        """Test successful title hierarchy retrieval."""
        hierarchy_response = {
            "data": {
                "title": "Software Engineer",
                "parents": [{"id": "100", "name": "Engineering"}],
                "children": [{"id": "124", "name": "Senior Software Engineer"}],
                "siblings": [{"id": "125", "name": "Data Engineer"}]
            }
        }

        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(hierarchy_response)

            result = await client.get_title_hierarchy("123")

            assert result["title"] == "Software Engineer"
            assert len(result["parents"]) == 1
            assert len(result["children"]) == 1
            assert len(result["siblings"]) == 1

    @pytest.mark.asyncio
    async def test_get_titles_metadata_success(self, mock_successful_response):
        """Test successful titles metadata retrieval."""
        metadata_response = {
            "data": {
                "version": "2023.4",
                "total_titles": 50000,
                "last_updated": "2023-12-01",
                "categories": ["Tech", "Healthcare", "Finance"]
            }
        }

        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(metadata_response)

            result = await client.get_titles_metadata()

            assert result["version"] == "2023.4"
            assert result["total_titles"] == 50000
            assert len(result["categories"]) == 3

    @pytest.mark.asyncio
    async def test_search_titles_empty_results(self, mock_successful_response):
        """Test title search with empty results."""
        empty_response = {"data": []}

        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(empty_response)

            results = await client.search_titles("nonexistent title")

            assert len(results) == 0
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_error_response):
        """Test API error handling."""
        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_error_response(400, "Bad Request")

            with pytest.raises(APIError) as exc_info:
                await client.search_titles("test query")

            assert "API request failed: 400" in str(exc_info.value)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, mock_error_response):
        """Test rate limit error handling."""
        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()

            # Mock a rate limit response directly
            import httpx
            from unittest.mock import MagicMock
            
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"RateLimit-Reset": "1640995200"}
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Too Many Requests", request=MagicMock(), response=mock_response
            )
            client.client.request.return_value = mock_response

            from src.mcp_lightcast.apis.base import RateLimitError
            with pytest.raises(RateLimitError) as exc_info:
                await client.search_titles("test query")

            assert "Rate limit exceeded" in str(exc_info.value)
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_search_titles_with_limit(self, mock_successful_response, sample_title_search_response):
        """Test title search with limit parameter."""
        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_search_response)

            await client.search_titles("engineer", limit=20)

            # Verify limit parameter was passed
            call_args = client.client.request.call_args
            params = call_args[1]["params"]
            assert params["limit"] == 20

    @pytest.mark.asyncio
    async def test_different_api_version(self, mock_successful_response, sample_title_search_response):
        """Test using different API version."""
        with patch('src.mcp_lightcast.apis.base.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})

            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_search_response)

            await client.search_titles("engineer", version="2024.1")

            # Verify the version was used in the URL
            call_args = client.client.request.call_args
            # URL is passed as a keyword argument
            url = call_args[1]["url"]
            assert "2024.1" in url
