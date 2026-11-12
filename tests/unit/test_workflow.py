"""Unit tests for title normalization and skills workflow."""

from unittest.mock import AsyncMock

import pytest

from src.mcp_lightcast.apis.classification import (
    SkillExtractionResult,
    SkillsExtractionResult,
)
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
    def normalized_title_response(self):
        """Titles API normalize response, as TitlesAPIClient.normalize_title returns it."""
        return {
            "data": {
                "confidence": 0.95,
                "title": {
                    "id": "title_123",
                    "name": "Software Engineer",
                    "type": "Tech",
                },
            }
        }

    @pytest.fixture
    def extracted_skills(self):
        """Classification API skills extraction result."""
        return SkillsExtractionResult(
            concepts=[
                SkillExtractionResult(
                    concept={
                        "id": "KS1200364C9C1LK3V5Q1",
                        "name": "Python",
                        "skillType": "Hard Skill",
                    },
                    confidence=0.85,
                ),
                SkillExtractionResult(
                    concept={"id": "KS1200770D9CT9WGXMPS", "name": "JavaScript"},
                    confidence=0.78,
                ),
            ]
        )

    def _workflow(self, clients):
        titles_client, classification_client, similarity_client = clients
        workflow = TitleNormalizationWorkflow()
        workflow.titles_client = titles_client
        workflow.classification_client = classification_client
        workflow.similarity_client = similarity_client
        return workflow

    @pytest.mark.asyncio
    async def test_workflow_success_complete(
        self, mock_workflow_clients, normalized_title_response, extracted_skills
    ):
        """Test complete successful workflow execution."""
        titles_client, classification_client, similarity_client = mock_workflow_clients
        titles_client.normalize_title.return_value = normalized_title_response
        classification_client.extract_skills_from_text.return_value = extracted_skills

        workflow = self._workflow(mock_workflow_clients)
        result = await workflow.normalize_title_and_get_skills("sr software dev")

        assert isinstance(result, NormalizedTitleWithSkills)
        assert result.raw_title == "sr software dev"
        assert result.normalized_title == {
            "id": "title_123",
            "name": "Software Engineer",
            "confidence": 0.95,
            "type": "Tech",
        }
        assert result.occupation_mappings == []
        assert result.skills == [
            {
                "id": "KS1200364C9C1LK3V5Q1",
                "name": "Python",
                "confidence": 0.85,
                "type": "Hard Skill",
            },
            {
                "id": "KS1200770D9CT9WGXMPS",
                "name": "JavaScript",
                "confidence": 0.78,
                "type": "Unknown",
            },
        ]

        assert result.workflow_metadata["steps_completed"] == [
            "title_normalization",
            "skills_extraction",
            "workflow_complete",
        ]
        assert result.workflow_metadata["errors"] == []
        assert result.workflow_metadata["summary"] == {
            "normalized_title_confidence": 0.95,
            "skills_count": 2,
        }

        titles_client.normalize_title.assert_called_once_with(
            "sr software dev", "latest"
        )
        classification_client.extract_skills_from_text.assert_called_once_with(
            "Software Engineer", confidence_threshold=0.5
        )
        similarity_client.get_occupation_skills.assert_not_called()

    @pytest.mark.asyncio
    async def test_workflow_unwrapped_normalize_response(
        self, mock_workflow_clients, extracted_skills
    ):
        """A normalize response without a "data" wrapper is used as is."""
        titles_client, classification_client, _ = mock_workflow_clients
        titles_client.normalize_title.return_value = {
            "confidence": 0.9,
            "title": {"id": "title_456", "name": "Data Scientist"},
        }
        classification_client.extract_skills_from_text.return_value = extracted_skills

        workflow = self._workflow(mock_workflow_clients)
        result = await workflow.normalize_title_and_get_skills("data scientist")

        assert result.normalized_title["id"] == "title_456"
        assert result.normalized_title["type"] is None
        assert len(result.skills) == 2

    @pytest.mark.asyncio
    async def test_workflow_partial_failure_skills(
        self, mock_workflow_clients, normalized_title_response
    ):
        """A skills extraction failure is recorded, and the normalized title still returned."""
        titles_client, classification_client, _ = mock_workflow_clients
        titles_client.normalize_title.return_value = normalized_title_response
        classification_client.extract_skills_from_text.side_effect = Exception(
            "API error"
        )

        workflow = self._workflow(mock_workflow_clients)
        result = await workflow.normalize_title_and_get_skills("software engineer")

        assert result.normalized_title["name"] == "Software Engineer"
        assert result.skills == []
        assert result.workflow_metadata["errors"] == [
            "Failed to extract skills: API error"
        ]
        assert "workflow_complete" not in result.workflow_metadata["steps_completed"]

    @pytest.mark.asyncio
    async def test_workflow_simple_version(
        self, mock_workflow_clients, normalized_title_response, extracted_skills
    ):
        """Test simplified workflow version."""
        titles_client, classification_client, _ = mock_workflow_clients
        titles_client.normalize_title.return_value = normalized_title_response
        classification_client.extract_skills_from_text.return_value = extracted_skills

        workflow = self._workflow(mock_workflow_clients)
        result = await workflow.get_title_skills_simple("software engineer", limit=1)

        assert result == {
            "normalized_title": "Software Engineer",
            "confidence": 0.95,
            "top_occupations": [],
            "skills": [{"name": "Python", "type": "Hard Skill", "category": None}],
            "skills_count": 2,
        }

    @pytest.mark.asyncio
    async def test_workflow_custom_parameters(
        self, mock_workflow_clients, normalized_title_response, extracted_skills
    ):
        """Test workflow with custom parameters."""
        titles_client, classification_client, _ = mock_workflow_clients
        titles_client.normalize_title.return_value = normalized_title_response
        classification_client.extract_skills_from_text.return_value = extracted_skills

        workflow = self._workflow(mock_workflow_clients)
        await workflow.normalize_title_and_get_skills(
            raw_title="software engineer",
            max_occupations=3,
            max_skills_per_occupation=50,
            skill_type="Hard Skill",
            confidence_threshold=0.8,
            version="2024.1",
        )

        titles_client.normalize_title.assert_called_once_with(
            "software engineer", "2024.1"
        )
        classification_client.extract_skills_from_text.assert_called_once_with(
            "Software Engineer", confidence_threshold=0.8
        )

    @pytest.mark.asyncio
    async def test_workflow_title_normalization_failure(self, mock_workflow_clients):
        """Test workflow when title normalization fails."""
        titles_client, classification_client, similarity_client = mock_workflow_clients

        titles_client.normalize_title.side_effect = Exception(
            "Title normalization failed"
        )

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
        workflow.titles_client.__aenter__ = AsyncMock(
            return_value=workflow.titles_client
        )
        workflow.titles_client.__aexit__ = AsyncMock(return_value=None)
        workflow.classification_client.__aenter__ = AsyncMock(
            return_value=workflow.classification_client
        )
        workflow.classification_client.__aexit__ = AsyncMock(return_value=None)
        workflow.similarity_client.__aenter__ = AsyncMock(
            return_value=workflow.similarity_client
        )
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
