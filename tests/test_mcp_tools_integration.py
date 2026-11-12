"""Opt-in metadata-only tests. For data operations use mcp_lightcast.diagnostics."""

import pytest
from fastmcp import Client

from mcp_lightcast.server import mcp

pytestmark = pytest.mark.live


@pytest.mark.parametrize(
    "tool",
    [
        "get_skills_metadata",
        "get_titles_metadata",
        "list_classification_releases",
        "get_similarity_metadata",
        "get_benchmark_metadata",
        "get_pathways_metadata",
        "get_postings_metadata",
    ],
)
async def test_live_metadata(tool):
    async with Client(mcp) as client:
        result = await client.call_tool(tool, {})
        assert result.data
