"""Integration tests for MCP Lightcast server."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

from fastmcp import FastMCP
from src.mcp_lightcast.server import mcp


class TestServerIntegration:
    """Integration tests for the complete MCP server."""
    
    @pytest.fixture
    def mock_lightcast_responses(self):
        """Mock all Lightcast API responses for integration testing."""
        responses = {
            "title_normalize": {
                "data": {
                    "id": "title_123",
                    "name": "Software Engineer", 
                    "confidence": 0.95,
                    "type": "Tech"
                }
            },
            "classification_map": {
                "data": [
                    {
                        "concept": "Software Engineer",
                        "confidence": 0.92,
                        "mapped_id": "15-1252.00",
                        "mapped_name": "Software Developers",
                        "mapping_type": "onet_soc"
                    }
                ]
            },
            "occupation_skills": {
                "data": {
                    "occupation_name": "Software Developers",
                    "skills": [
                        {
                            "id": "KS1200364C9C1LK3V5Q1",
                            "name": "Python",
                            "type": "Hard Skill",
                            "category": "Information Technology",
                            "importance": 0.85
                        },
                        {
                            "id": "KS1200770D9CT9WGXMPS",
                            "name": "JavaScript",
                            "type": "Hard Skill", 
                            "category": "Information Technology",
                            "importance": 0.78
                        }
                    ],
                    "total_skills": 2
                }
            },
            "title_search": {
                "data": [
                    {
                        "id": "1",
                        "name": "Software Engineer",
                        "type": "Tech"
                    },
                    {
                        "id": "2",
                        "name": "Senior Software Engineer", 
                        "type": "Tech"
                    }
                ]
            },
            "skill_search": {
                "data": [
                    {
                        "id": "KS1200364C9C1LK3V5Q1",
                        "name": "Python",
                        "type": "Hard Skill",
                        "category": "Information Technology",
                        "subcategory": "Programming Languages"
                    }
                ]
            }
        }
        return responses
    
    @pytest.fixture
    def mock_api_clients(self, mock_lightcast_responses):
        """Mock all API clients for integration testing."""
        with patch('src.mcp_lightcast.auth.oauth.lightcast_auth') as mock_auth:
            mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test_token"}
            
            # Mock HTTP client responses
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                def mock_request(method, url, **kwargs):
                    response = MagicMock()
                    response.status_code = 200
                    response.headers = {"content-type": "application/json"}
                    response.raise_for_status.return_value = None
                    
                    # Return appropriate response based on URL
                    if "normalize" in url:
                        response.json.return_value = mock_lightcast_responses["title_normalize"]
                    elif "map_concepts" in url:
                        response.json.return_value = mock_lightcast_responses["classification_map"]
                    elif "skills" in url and "occupations" in url:
                        response.json.return_value = mock_lightcast_responses["occupation_skills"]
                    elif "titles" in url:
                        response.json.return_value = mock_lightcast_responses["title_search"]
                    elif "skills" in url:
                        response.json.return_value = mock_lightcast_responses["skill_search"]
                    else:
                        response.json.return_value = {"data": []}
                    
                    return response
                
                mock_client.request.side_effect = mock_request
                yield mock_client
    
    @pytest.mark.asyncio
    async def test_normalize_title_and_get_skills_tool(self, mock_api_clients):
        """Test the complete normalize title and get skills workflow tool."""
        # Get the tool function from the server
        tool_registry = mcp._tools
        assert "normalize_title_and_get_skills" in tool_registry
        
        tool_func = tool_registry["normalize_title_and_get_skills"]
        
        # Execute the tool
        result = await tool_func("sr software dev")
        
        # Verify the complete workflow result
        assert "raw_title" in result
        assert "normalized_title" in result
        assert "occupation_mappings" in result
        assert "skills" in result
        assert "metadata" in result
        
        assert result["raw_title"] == "sr software dev"
        assert result["normalized_title"]["name"] == "Software Engineer"
        assert result["normalized_title"]["confidence"] == 0.95
        assert len(result["occupation_mappings"]) == 1
        assert result["occupation_mappings"][0]["occupation_name"] == "Software Developers"
        assert len(result["skills"]) == 2
        
        # Verify skills have source occupation information
        for skill in result["skills"]:
            assert "source_occupations" in skill
            assert len(skill["source_occupations"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_title_skills_simple_tool(self, mock_api_clients):
        """Test the simplified title skills tool."""
        tool_registry = mcp._tools
        assert "get_title_skills_simple" in tool_registry
        
        tool_func = tool_registry["get_title_skills_simple"]
        result = await tool_func("software engineer")
        
        # Verify simplified result structure
        assert "normalized_title" in result
        assert "confidence" in result
        assert "top_occupations" in result
        assert "skills" in result
        assert "skills_count" in result
        
        assert result["normalized_title"] == "Software Engineer"
        assert result["confidence"] == 0.95
        assert "Software Developers" in result["top_occupations"]
        assert result["skills_count"] == 2
    
    @pytest.mark.asyncio
    async def test_search_job_titles_tool(self, mock_api_clients):
        """Test the job title search tool."""
        tool_registry = mcp._tools
        assert "search_job_titles" in tool_registry
        
        tool_func = tool_registry["search_job_titles"]
        result = await tool_func("software engineer", limit=5)
        
        # Verify search results
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Software Engineer"
        assert result[1]["name"] == "Senior Software Engineer"
    
    @pytest.mark.asyncio
    async def test_normalize_job_title_tool(self, mock_api_clients):
        """Test the job title normalization tool."""
        tool_registry = mcp._tools
        assert "normalize_job_title" in tool_registry
        
        tool_func = tool_registry["normalize_job_title"]
        result = await tool_func("sr software dev")
        
        # Verify normalization result
        assert "normalized_title" in result
        assert "original_title" in result
        assert result["original_title"] == "sr software dev"
        assert result["normalized_title"]["name"] == "Software Engineer"
        assert result["normalized_title"]["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_search_skills_tool(self, mock_api_clients):
        """Test the skills search tool."""
        tool_registry = mcp._tools
        assert "search_skills" in tool_registry
        
        tool_func = tool_registry["search_skills"]
        result = await tool_func("python", limit=10)
        
        # Verify skills search results
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["type"] == "Hard Skill"
        assert result[0]["category"] == "Information Technology"
    
    @pytest.mark.asyncio
    async def test_server_health_check(self, mock_api_clients):
        """Test server health check resource."""
        resource_registry = mcp._resources
        assert "server/health" in resource_registry
        
        health_func = resource_registry["server/health"]
        result = await health_func()
        
        # Verify health check response
        assert "status" in result
        assert "authentication" in result
        assert "timestamp" in result
        assert result["status"] == "healthy"
        assert result["authentication"] == "configured"
    
    @pytest.mark.asyncio
    async def test_server_info_resource(self, mock_api_clients):
        """Test server info resource."""
        resource_registry = mcp._resources
        assert "server/info" in resource_registry
        
        info_func = resource_registry["server/info"]
        result = await info_func()
        
        # Verify server info
        assert "name" in result
        assert "description" in result
        assert "version" in result
        assert "supported_apis" in result
        assert len(result["supported_apis"]) >= 5
        assert "Titles API" in str(result["supported_apis"])
        assert "Skills API" in str(result["supported_apis"])
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_api_clients):
        """Test error handling in the integrated system."""
        # Modify mock to raise an error
        mock_api_clients.request.side_effect = Exception("API temporarily unavailable")
        
        tool_registry = mcp._tools
        tool_func = tool_registry["search_job_titles"]
        
        # The error should be handled by the server's error handler
        with pytest.raises(Exception):
            await tool_func("test query")
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, mock_api_clients):
        """Test concurrent execution of multiple tools."""
        tool_registry = mcp._tools
        
        # Execute multiple tools concurrently
        search_task = tool_registry["search_job_titles"]("engineer")
        normalize_task = tool_registry["normalize_job_title"]("sr dev")
        skills_task = tool_registry["search_skills"]("python")
        
        search_result, normalize_result, skills_result = await asyncio.gather(
            search_task, normalize_task, skills_task
        )
        
        # Verify all results
        assert len(search_result) == 2
        assert normalize_result["normalized_title"]["name"] == "Software Engineer"
        assert len(skills_result) == 1
        assert skills_result[0]["name"] == "Python"
    
    @pytest.mark.asyncio
    async def test_workflow_with_custom_parameters(self, mock_api_clients):
        """Test workflow tool with custom parameters."""
        tool_registry = mcp._tools
        tool_func = tool_registry["normalize_title_and_get_skills"]
        
        result = await tool_func(
            "data scientist",
            max_occupations=3,
            max_skills_per_occupation=30,
            skill_type="Hard Skill",
            confidence_threshold=0.8
        )
        
        # Verify the result structure remains correct with custom parameters
        assert result["raw_title"] == "data scientist"
        assert "normalized_title" in result
        assert "occupation_mappings" in result
        assert "skills" in result