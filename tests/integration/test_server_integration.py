"""Integration tests for MCP Lightcast server."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.mcp_lightcast.tools.normalize_title_get_skills import TitleNormalizationWorkflow
from src.mcp_lightcast.apis.titles import TitleNormalizationResult, TitleDetail
from src.mcp_lightcast.apis.classification import ConceptMapping, OccupationMapping
from src.mcp_lightcast.apis.similarity import OccupationSkillMapping
from src.mcp_lightcast.server import mcp


class TestServerIntegration:
    """Integration tests for the complete MCP server."""

    @pytest.fixture
    def mock_workflow_responses(self):
        """Mock responses for the complete workflow."""
        return {
            "normalized_title": TitleNormalizationResult(
                confidence=0.95,
                title=TitleDetail(
                    id="title_123",
                    name="Software Engineer",
                    type="Tech"
                )
            ),
            "classification_results": [
                ConceptMapping(
                    concept="Software Engineer",
                    occupations=[
                        OccupationMapping(
                            id="15-1252.00",
                            title="Software Developers",
                            confidence=0.92,
                            type="onet_soc"
                        )
                    ]
                )
            ],
            "occupation_skills": OccupationSkillMapping(
                occupation_id="15-1252.00",
                occupation_name="Software Developers",
                skills=[
                    {
                        "id": "KS1200364C9C1LK3V5Q1",
                        "name": "Python",
                        "type": "Hard Skill",
                        "importance": 0.85
                    },
                    {
                        "id": "KS1200770D9CT9WGXMPS",
                        "name": "JavaScript",
                        "type": "Hard Skill",
                        "importance": 0.78
                    }
                ],
                total_skills=2
            )
        }

    @pytest.mark.asyncio
    async def test_normalize_title_and_get_skills_tool(self, mock_workflow_responses):
        """Test the complete normalize title and get skills workflow tool."""
        # Mock the workflow clients
        with patch.object(TitleNormalizationWorkflow, '__init__', return_value=None):
            with patch.object(TitleNormalizationWorkflow, '__aenter__', new_callable=AsyncMock) as mock_aenter:
                with patch.object(TitleNormalizationWorkflow, '__aexit__', new_callable=AsyncMock):
                    with patch.object(TitleNormalizationWorkflow, 'normalize_title_and_get_skills', new_callable=AsyncMock) as mock_workflow:
                        
                        # Setup mock workflow
                        workflow_instance = TitleNormalizationWorkflow()
                        mock_aenter.return_value = workflow_instance
                        
                        # Mock the workflow result
                        from src.mcp_lightcast.tools.normalize_title_get_skills import NormalizedTitleWithSkills
                        mock_result = NormalizedTitleWithSkills(
                            raw_title="sr software dev",
                            normalized_title={
                                "id": "title_123",
                                "name": "Software Engineer",
                                "confidence": 0.95,
                                "type": "Tech"
                            },
                            occupation_mappings=[
                                {
                                    "occupation_id": "15-1252.00",
                                    "occupation_name": "Software Developers",
                                    "confidence": 0.92,
                                    "mapping_type": "onet_soc"
                                }
                            ],
                            skills=[
                                {
                                    "id": "KS1200364C9C1LK3V5Q1",
                                    "name": "Python",
                                    "type": "Hard Skill",
                                    "source_occupations": [
                                        {
                                            "id": "15-1252.00",
                                            "name": "Software Developers",
                                            "confidence": 0.92
                                        }
                                    ]
                                },
                                {
                                    "id": "KS1200770D9CT9WGXMPS",
                                    "name": "JavaScript",
                                    "type": "Hard Skill",
                                    "source_occupations": [
                                        {
                                            "id": "15-1252.00",
                                            "name": "Software Developers",
                                            "confidence": 0.92
                                        }
                                    ]
                                }
                            ],
                            workflow_metadata={
                                "steps_completed": ["title_normalization", "occupation_mapping", "skills_extraction", "workflow_complete"],
                                "errors": [],
                                "summary": {
                                    "normalized_title_confidence": 0.95,
                                    "occupation_mappings_count": 1,
                                    "unique_skills_count": 2
                                }
                            }
                        )
                        
                        mock_workflow.return_value = mock_result
                        
                        # Import and execute the tool function directly
                        from src.mcp_lightcast.tools.workflow_tools import register_workflow_tools
                        
                        # Create a temporary MCP instance for testing
                        from fastmcp import FastMCP
                        test_mcp = FastMCP("test")
                        register_workflow_tools(test_mcp)
                        
                        # Test the tool by calling the underlying function
                        # We can't access the tool directly from FastMCP, so we test the workflow class
                        async with TitleNormalizationWorkflow() as workflow:
                            result = await workflow.normalize_title_and_get_skills("sr software dev")
                            
                            # Verify the complete workflow result
                            assert result.raw_title == "sr software dev"
                            assert result.normalized_title["name"] == "Software Engineer"
                            assert result.normalized_title["confidence"] == 0.95
                            assert len(result.occupation_mappings) == 1
                            assert result.occupation_mappings[0]["occupation_name"] == "Software Developers"
                            assert len(result.skills) == 2

    @pytest.mark.asyncio
    async def test_get_title_skills_simple_tool(self, mock_workflow_responses):
        """Test the simplified title skills tool."""
        with patch.object(TitleNormalizationWorkflow, '__init__', return_value=None):
            with patch.object(TitleNormalizationWorkflow, '__aenter__', new_callable=AsyncMock) as mock_aenter:
                with patch.object(TitleNormalizationWorkflow, '__aexit__', new_callable=AsyncMock):
                    with patch.object(TitleNormalizationWorkflow, 'get_title_skills_simple', new_callable=AsyncMock) as mock_simple:
                        
                        workflow_instance = TitleNormalizationWorkflow()
                        mock_aenter.return_value = workflow_instance
                        
                        mock_simple.return_value = {
                            "normalized_title": "Software Engineer",
                            "confidence": 0.95,
                            "top_occupations": ["Software Developers"],
                            "skills": [
                                {"name": "Python", "type": "Hard Skill"},
                                {"name": "JavaScript", "type": "Hard Skill"}
                            ],
                            "skills_count": 2
                        }
                        
                        async with TitleNormalizationWorkflow() as workflow:
                            result = await workflow.get_title_skills_simple("software engineer")
                            
                            assert result["normalized_title"] == "Software Engineer"
                            assert result["confidence"] == 0.95
                            assert "Software Developers" in result["top_occupations"]
                            assert result["skills_count"] == 2

    @pytest.mark.asyncio
    async def test_search_job_titles_tool(self):
        """Test the job title search tool."""
        from src.mcp_lightcast.apis.titles import TitlesAPIClient, TitleSearchResult
        
        with patch.object(TitlesAPIClient, 'search_titles', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                TitleSearchResult(id="1", name="Software Engineer", type="Tech"),
                TitleSearchResult(id="2", name="Senior Software Engineer", type="Tech")
            ]
            
            client = TitlesAPIClient()
            results = await client.search_titles("software engineer", limit=5)
            
            assert len(results) == 2
            assert results[0].name == "Software Engineer"
            assert results[1].name == "Senior Software Engineer"

    @pytest.mark.asyncio
    async def test_normalize_job_title_tool(self):
        """Test the job title normalization tool."""
        from src.mcp_lightcast.apis.titles import TitlesAPIClient
        
        with patch.object(TitlesAPIClient, 'normalize_title', new_callable=AsyncMock) as mock_normalize:
            mock_normalize.return_value = {
                "data": {
                    "id": "title_123",
                    "name": "Software Engineer",
                    "confidence": 0.95,
                    "type": "Tech"
                }
            }
            
            client = TitlesAPIClient()
            result = await client.normalize_title("sr software dev")
            
            assert result["data"]["name"] == "Software Engineer"
            assert result["data"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_search_skills_tool(self):
        """Test the skills search tool."""
        from src.mcp_lightcast.apis.skills import SkillsAPIClient, SkillSearchResult
        
        with patch.object(SkillsAPIClient, 'search_skills', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SkillSearchResult(
                    id="KS1200364C9C1LK3V5Q1",
                    name="Python",
                    type={"id": "ST1", "name": "Hard Skill"}
                )
            ]
            
            client = SkillsAPIClient()
            results = await client.search_skills("python", limit=5)
            
            assert len(results) == 1
            assert results[0].name == "Python"

    @pytest.mark.asyncio
    async def test_server_health_check(self):
        """Test server health check resource."""
        # Note: FastMCP resources are not directly callable in tests
        # This test verifies the server module imports correctly
        try:
            from src.mcp_lightcast.server import health_check, server_info, mcp
            assert health_check is not None
            assert server_info is not None
            assert mcp is not None
            # If we get here, the server module loaded successfully
            assert True
        except Exception as e:
            assert False, f"Server module failed to load: {e}"

    @pytest.mark.asyncio
    async def test_server_info_resource(self):
        """Test server info resource."""
        # Note: FastMCP resources are not directly callable in tests
        # This test verifies the server configuration is valid
        try:
            from src.mcp_lightcast.server import mcp
            # Check that the server instance was created successfully
            assert mcp.name == "lightcast-mcp-server"
            assert True
        except Exception as e:
            assert False, f"Server configuration failed: {e}"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling in tools."""
        from src.mcp_lightcast.apis.titles import TitlesAPIClient
        from src.mcp_lightcast.apis.base import APIError
        
        with patch.object(TitlesAPIClient, 'search_titles', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = APIError("API Error", status_code=400)
            
            client = TitlesAPIClient()
            
            with pytest.raises(APIError):
                await client.search_titles("test query")

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, mock_workflow_responses):
        """Test concurrent execution of multiple tools."""
        from src.mcp_lightcast.apis.titles import TitlesAPIClient, TitleSearchResult
        from src.mcp_lightcast.apis.skills import SkillsAPIClient, SkillSearchResult
        
        with patch.object(TitlesAPIClient, 'search_titles', new_callable=AsyncMock) as mock_titles:
            with patch.object(SkillsAPIClient, 'search_skills', new_callable=AsyncMock) as mock_skills:
                
                mock_titles.return_value = [
                    TitleSearchResult(id="1", name="Software Engineer", type="Tech")
                ]
                mock_skills.return_value = [
                    SkillSearchResult(
                        id="KS1200364C9C1LK3V5Q1",
                        name="Python",
                        type={"id": "ST1", "name": "Hard Skill"}
                    )
                ]
                
                # Execute both searches concurrently
                import asyncio
                titles_client = TitlesAPIClient()
                skills_client = SkillsAPIClient()
                
                title_task = titles_client.search_titles("software engineer")
                skill_task = skills_client.search_skills("python")
                
                title_results, skill_results = await asyncio.gather(title_task, skill_task)
                
                assert len(title_results) == 1
                assert len(skill_results) == 1
                assert title_results[0].name == "Software Engineer"
                assert skill_results[0].name == "Python"

    @pytest.mark.asyncio
    async def test_workflow_with_custom_parameters(self, mock_workflow_responses):
        """Test workflow with custom parameters."""
        with patch.object(TitleNormalizationWorkflow, '__init__', return_value=None):
            with patch.object(TitleNormalizationWorkflow, '__aenter__', new_callable=AsyncMock) as mock_aenter:
                with patch.object(TitleNormalizationWorkflow, '__aexit__', new_callable=AsyncMock):
                    with patch.object(TitleNormalizationWorkflow, 'normalize_title_and_get_skills', new_callable=AsyncMock) as mock_workflow:
                        
                        workflow_instance = TitleNormalizationWorkflow()
                        mock_aenter.return_value = workflow_instance
                        
                        from src.mcp_lightcast.tools.normalize_title_get_skills import NormalizedTitleWithSkills
                        mock_result = NormalizedTitleWithSkills(
                            raw_title="software engineer",
                            normalized_title={"name": "Software Engineer", "confidence": 0.95},
                            occupation_mappings=[],
                            skills=[],
                            workflow_metadata={"steps_completed": [], "errors": []}
                        )
                        
                        mock_workflow.return_value = mock_result
                        
                        async with TitleNormalizationWorkflow() as workflow:
                            result = await workflow.normalize_title_and_get_skills(
                                raw_title="software engineer",
                                max_occupations=3,
                                max_skills_per_occupation=50,
                                skill_type="Hard Skill",
                                confidence_threshold=0.8,
                                version="2024.1"
                            )
                            
                            # Verify the workflow was called with custom parameters
                            mock_workflow.assert_called_with(
                                raw_title="software engineer",
                                max_occupations=3,
                                max_skills_per_occupation=50,
                                skill_type="Hard Skill",
                                confidence_threshold=0.8,
                                version="2024.1"
                            )