"""Unit tests for Titles API client."""

import pytest
from unittest.mock import AsyncMock, patch

from src.mcp_lightcast.apis.titles import TitlesAPIClient, TitleSearchResult, TitleDetail, TitleNormalizationResult
from src.mcp_lightcast.apis.base import APIError


class TestTitlesAPIClient:
    """Test cases for TitlesAPIClient."""
    
    @pytest.mark.asyncio
    async def test_search_titles_success(self, mock_successful_response, sample_title_search_response):
        """Test successful title search."""
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
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
        
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
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
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_normalize_response)
            
            result = await client.normalize_title("sr software dev")
            
            assert isinstance(result, TitleNormalizationResult)
            assert result.id == "123"
            assert result.name == "Software Engineer"
            assert result.confidence == 0.95
            
            # Verify the request was made with text content
            client.client.request.assert_called_once()
            call_args = client.client.request.call_args
            assert call_args[1]["content"] == "sr software dev"
            assert call_args[1]["headers"]["Content-Type"] == "text/plain"
    
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
        
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
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
        
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
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
        
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(empty_response)
            
            results = await client.search_titles("nonexistent title")
            
            assert len(results) == 0
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_error_response):
        """Test API error handling."""
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
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
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
            client = TitlesAPIClient()
            client.client = AsyncMock()
            
            # Create a rate limit response
            rate_limit_response = mock_error_response(429, "Too Many Requests")
            rate_limit_response.headers = {"RateLimit-Reset": "1640995200"}
            client.client.request.return_value = rate_limit_response
            
            from src.mcp_lightcast.apis.base import RateLimitError
            with pytest.raises(RateLimitError) as exc_info:
                await client.search_titles("test query")
            
            assert "Rate limit exceeded" in str(exc_info.value)
            assert exc_info.value.status_code == 429
    
    @pytest.mark.asyncio
    async def test_search_titles_with_pagination(self, mock_successful_response, sample_title_search_response):
        """Test title search with pagination parameters."""
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_search_response)
            
            results = await client.search_titles("engineer", limit=20, offset=40)
            
            # Verify pagination parameters were passed
            call_args = client.client.request.call_args
            params = call_args[1]["params"]
            assert params["limit"] == 20
            assert params["offset"] == 40
    
    @pytest.mark.asyncio
    async def test_different_api_version(self, mock_successful_response, sample_title_search_response):
        """Test using different API version."""
        with patch('src.mcp_lightcast.apis.titles.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
            
            client = TitlesAPIClient()
            client.client = AsyncMock()
            client.client.request.return_value = mock_successful_response(sample_title_search_response)
            
            await client.search_titles("engineer", version="2024.1")
            
            # Verify the version was used in the URL
            call_args = client.client.request.call_args
            url = call_args[0][1]
            assert "2024.1" in url