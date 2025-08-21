"""Pytest configuration and fixtures for MCP Lightcast tests."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.mcp_lightcast.apis.classification import ClassificationAPIClient
from src.mcp_lightcast.apis.similarity import SimilarityAPIClient
from src.mcp_lightcast.apis.skills import SkillsAPIClient
from src.mcp_lightcast.apis.titles import TitlesAPIClient
from src.mcp_lightcast.auth.oauth import LightcastAuth


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    auth = MagicMock(spec=LightcastAuth)
    auth.get_access_token = AsyncMock(return_value="mock_access_token")
    auth.get_auth_headers = AsyncMock(return_value={
        "Authorization": "Bearer mock_access_token",
        "Content-Type": "application/json"
    })
    return auth


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def sample_title_search_response():
    """Sample response for title search."""
    return {
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
    }


@pytest.fixture
def sample_title_normalize_response():
    """Sample response for title normalization."""
    return {
        "data": {
            "id": "123",
            "name": "Software Engineer",
            "confidence": 0.95,
            "type": "Tech"
        }
    }


@pytest.fixture
def sample_skill_search_response():
    """Sample response for skill search."""
    return {
        "data": [
            {
                "id": "KS1200364C9C1LK3V5Q1",
                "name": "Python",
                "type": "Hard Skill",
                "category": "Information Technology",
                "subcategory": "Programming Languages"
            },
            {
                "id": "KS1200770D9CT9WGXMPS",
                "name": "JavaScript",
                "type": "Hard Skill",
                "category": "Information Technology",
                "subcategory": "Programming Languages"
            }
        ]
    }


@pytest.fixture
def sample_classification_response():
    """Sample response for classification mapping."""
    return {
        "data": [
            {
                "concept": "Software Engineer",
                "confidence": 0.92,
                "mapped_id": "15-1252.00",
                "mapped_name": "Software Developers",
                "mapping_type": "onet_soc"
            }
        ]
    }


@pytest.fixture
def sample_occupation_skills_response():
    """Sample response for occupation skills."""
    return {
        "data": {
            "occupation_name": "Software Developers",
            "skills": [
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
            "total_skills": 2
        }
    }


@pytest.fixture
def mock_titles_client(mock_httpx_client, mock_auth):
    """Mock titles API client."""
    client = TitlesAPIClient()
    client.client = mock_httpx_client
    client._auth = mock_auth
    return client


@pytest.fixture
def mock_skills_client(mock_httpx_client, mock_auth):
    """Mock skills API client."""
    client = SkillsAPIClient()
    client.client = mock_httpx_client
    client._auth = mock_auth
    return client


@pytest.fixture
def mock_classification_client(mock_httpx_client, mock_auth):
    """Mock classification API client."""
    client = ClassificationAPIClient()
    client.client = mock_httpx_client
    client._auth = mock_auth
    return client


@pytest.fixture
def mock_similarity_client(mock_httpx_client, mock_auth):
    """Mock similarity API client."""
    client = SimilarityAPIClient()
    client.client = mock_httpx_client
    client._auth = mock_auth
    return client


@pytest.fixture
def mock_successful_response():
    """Create a mock successful HTTP response."""
    def _create_response(json_data: dict[str, Any], status_code: int = 200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data
        response.headers = {"content-type": "application/json"}
        response.raise_for_status.return_value = None
        return response
    return _create_response


@pytest.fixture
def mock_error_response():
    """Create a mock error HTTP response."""
    def _create_error_response(status_code: int = 400, error_message: str = "Bad Request"):
        response = MagicMock()
        response.status_code = status_code
        response.reason_phrase = error_message
        response.json.return_value = {"error": error_message}
        response.headers = {"content-type": "application/json"}
        response.text = error_message

        def raise_for_status():
            from httpx import HTTPStatusError
            raise HTTPStatusError(error_message, request=MagicMock(), response=response)

        response.raise_for_status.side_effect = raise_for_status
        return response
    return _create_error_response
