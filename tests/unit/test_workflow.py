"""Unit tests for title normalization and skills workflow."""

from unittest.mock import AsyncMock

import pytest

from src.mcp_lightcast.apis.classification import ConceptMapping, OccupationMapping
from src.mcp_lightcast.apis.similarity import OccupationSkillMapping
from src.mcp_lightcast.apis.titles import TitleDetail, TitleNormalizationResult
from src.mcp_lightcast.tools.normalize_title_get_skills import (
    NormalizedTitleWithSkills,
    TitleNormalizationWorkflow,
)


class TestTitleNormalizationWorkflow:
    """Test cases for TitleNormalizationWorkflow."""

    @pytest.fixture
    def mock_workflow_clients(self):
        """Create mock clients for the workflow."""
        titles_client = AsyncMock()
        classification_client = AsyncMock()
        similarity_client = AsyncMock()

        return titles_client, classification_client, similarity_client

    @pytest.fixture
    def sample_workflow_data(self):
        """Sample data for workflow testing."""
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
    async def test_workflow_success_complete(self, mock_workflow_clients, sample_workflow_data):
        """Test complete successful workflow execution."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        # Configure mock responses
        titles_client.normalize_title.return_value = sample_workflow_data["normalized_title"]
        classification_client.map_concepts.return_value = sample_workflow_data["classification_results"]
        similarity_client.get_occupation_skills.return_value = sample_workflow_data["occupation_skills"]

        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client

        result = await workflow.normalize_title_and_get_skills("sr software dev")

        # Verify result structure
        assert isinstance(result, NormalizedTitleWithSkills)
        assert result.raw_title == "sr software dev"
        assert result.normalized_title["name"] == "Software Engineer"
        assert result.normalized_title["confidence"] == 0.95
        assert len(result.occupation_mappings) == 1
        assert result.occupation_mappings[0]["occupation_id"] == "15-1252.00"
        assert len(result.skills) == 2

        # Verify workflow metadata
        assert "workflow_complete" in result.workflow_metadata["steps_completed"]
        assert len(result.workflow_metadata["errors"]) == 0
        assert result.workflow_metadata["summary"]["unique_skills_count"] == 2

        # Verify API calls were made
        titles_client.normalize_title.assert_called_once_with("sr software dev", "2023.4")
        classification_client.map_concepts.assert_called_once()
        similarity_client.get_occupation_skills.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_skill_deduplication(self, mock_workflow_clients):
        """Test that duplicate skills are properly deduplicated."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        # Setup normalized title
        titles_client.normalize_title.return_value = TitleNormalizationResult(
            confidence=0.95,
            title=TitleDetail(
                id="title_123",
                name="Software Engineer",
                type="Tech"
            )
        )

        # Setup multiple occupation mappings
        classification_client.map_concepts.return_value = [
            ConceptMapping(
                concept="Software Engineer",
                occupations=[
                    OccupationMapping(
                        id="15-1252.00",
                        title="Software Developers",
                        confidence=0.92,
                        type="onet_soc"
                    ),
                    OccupationMapping(
                        id="15-1253.00",
                        title="Software Quality Assurance Analysts",
                        confidence=0.88,
                        type="onet_soc"
                    )
                ]
            )
        ]

        # Setup overlapping skills between occupations
        def mock_get_occupation_skills(occupation_id, **kwargs):
            if occupation_id == "15-1252.00":
                return OccupationSkillMapping(
                    occupation_id=occupation_id,
                    occupation_name="Software Developers",
                    skills=[
                        {"id": "skill_1", "name": "Python", "type": "Hard Skill"},
                        {"id": "skill_2", "name": "JavaScript", "type": "Hard Skill"}
                    ],
                    total_skills=2
                )
            else:
                return OccupationSkillMapping(
                    occupation_id=occupation_id,
                    occupation_name="Software Quality Assurance Analysts",
                    skills=[
                        {"id": "skill_1", "name": "Python", "type": "Hard Skill"},  # Duplicate
                        {"id": "skill_3", "name": "Testing", "type": "Hard Skill"}
                    ],
                    total_skills=2
                )

        similarity_client.get_occupation_skills.side_effect = mock_get_occupation_skills

        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client

        result = await workflow.normalize_title_and_get_skills("software engineer")

        # Should have 3 unique skills (Python, JavaScript, Testing)
        assert len(result.skills) == 3
        skill_names = {skill["name"] for skill in result.skills}
        assert skill_names == {"Python", "JavaScript", "Testing"}

        # Python skill should have source_occupations from both occupations
        python_skill = next(skill for skill in result.skills if skill["name"] == "Python")
        assert len(python_skill["source_occupations"]) == 2

    @pytest.mark.asyncio
    async def test_workflow_partial_failure_skills(self, mock_workflow_clients, sample_workflow_data):
        """Test workflow when skills retrieval fails for some occupations."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        titles_client.normalize_title.return_value = sample_workflow_data["normalized_title"]

        # Multiple occupation mappings
        classification_client.map_concepts.return_value = [
            ConceptMapping(
                concept="Software Engineer",
                occupations=[
                    OccupationMapping(
                        id="15-1252.00",
                        title="Software Developers",
                        confidence=0.92,
                        type="onet_soc"
                    ),
                    OccupationMapping(
                        id="15-1253.00",
                        title="Software Quality Assurance Analysts",
                        confidence=0.88,
                        type="onet_soc"
                    )
                ]
            )
        ]

        # First occupation succeeds, second fails
        def mock_get_occupation_skills(occupation_id, **kwargs):
            if occupation_id == "15-1252.00":
                return sample_workflow_data["occupation_skills"]
            else:
                raise Exception("API error for this occupation")

        similarity_client.get_occupation_skills.side_effect = mock_get_occupation_skills

        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client

        result = await workflow.normalize_title_and_get_skills("software engineer")

        # Should still complete with partial results
        assert len(result.occupation_mappings) == 2
        assert len(result.skills) == 2  # Only from successful occupation
        assert len(result.workflow_metadata["errors"]) == 1
        assert "Failed to get skills for 15-1253.00" in result.workflow_metadata["errors"][0]

    @pytest.mark.asyncio
    async def test_workflow_simple_version(self, mock_workflow_clients, sample_workflow_data):
        """Test simplified workflow version."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        titles_client.normalize_title.return_value = sample_workflow_data["normalized_title"]
        classification_client.map_concepts.return_value = sample_workflow_data["classification_results"]
        similarity_client.get_occupation_skills.return_value = sample_workflow_data["occupation_skills"]

        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client

        result = await workflow.get_title_skills_simple("software engineer", limit=10)

        # Verify simplified structure
        assert "normalized_title" in result
        assert "confidence" in result
        assert "top_occupations" in result
        assert "skills" in result
        assert "skills_count" in result

        assert result["normalized_title"] == "Software Engineer"
        assert result["confidence"] == 0.95
        assert len(result["top_occupations"]) == 1
        assert result["top_occupations"][0] == "Software Developers"
        assert len(result["skills"]) <= 10

    @pytest.mark.asyncio
    async def test_workflow_custom_parameters(self, mock_workflow_clients, sample_workflow_data):
        """Test workflow with custom parameters."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        titles_client.normalize_title.return_value = sample_workflow_data["normalized_title"]
        classification_client.map_concepts.return_value = sample_workflow_data["classification_results"]
        similarity_client.get_occupation_skills.return_value = sample_workflow_data["occupation_skills"]

        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client

        result = await workflow.normalize_title_and_get_skills(
            raw_title="software engineer",
            max_occupations=3,
            max_skills_per_occupation=50,
            skill_type="Hard Skill",
            confidence_threshold=0.8,
            version="2024.1"
        )

        # Verify custom parameters were passed to API calls
        classification_client.map_concepts.assert_called_with(
            concepts=["Software Engineer"],
            target_taxonomy="onet_soc",
            limit=3,
            confidence_threshold=0.8,
            version="2024.1"
        )

        similarity_client.get_occupation_skills.assert_called_with(
            occupation_id="15-1252.00",
            limit=50,
            skill_type="Hard Skill",
            version="2024.1"
        )

    @pytest.mark.asyncio
    async def test_workflow_title_normalization_failure(self, mock_workflow_clients):
        """Test workflow when title normalization fails."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        titles_client.normalize_title.side_effect = Exception("Title normalization failed")

        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client

        with pytest.raises(Exception) as exc_info:
            await workflow.normalize_title_and_get_skills("invalid title")

        assert "Title normalization failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_workflow_context_manager(self):
        """Test workflow context manager functionality."""
        workflow = TitleNormalizationWorkflow()

        # Mock the clients' context manager methods
        workflow.titles_client.__aenter__ = AsyncMock(return_value=workflow.titles_client)
        workflow.titles_client.__aexit__ = AsyncMock(return_value=None)
        workflow.classification_client.__aenter__ = AsyncMock(return_value=workflow.classification_client)
        workflow.classification_client.__aexit__ = AsyncMock(return_value=None)
        workflow.similarity_client.__aenter__ = AsyncMock(return_value=workflow.similarity_client)
        workflow.similarity_client.__aexit__ = AsyncMock(return_value=None)

        async with workflow:
            # Verify all clients were entered
            workflow.titles_client.__aenter__.assert_called_once()
            workflow.classification_client.__aenter__.assert_called_once()
            workflow.similarity_client.__aenter__.assert_called_once()

        # Verify all clients were exited
        workflow.titles_client.__aexit__.assert_called_once()
        workflow.classification_client.__aexit__.assert_called_once()
        workflow.similarity_client.__aexit__.assert_called_once()
