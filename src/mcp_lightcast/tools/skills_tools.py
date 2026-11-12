"""MCP tools for skills lookup and text extraction."""

from typing import Any

from fastmcp import FastMCP

from ..apis.similarity import SimilarityAPIClient
from ..apis.skills import SkillsAPIClient
from .types import READ_ONLY, Confidence, IDs, Limit, Text


def register_skills_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"skills"}, annotations=READ_ONLY)
    async def search_skills(
        query: Text,
        limit: Limit = 10,
        skill_type: str | None = None,
        version: Text = "latest",
    ) -> list[dict[str, Any]]:
        """Search the Skills taxonomy. skill_type accepts type IDs: ST1 (specialized), ST2 (common), ST3 (certification), comma-separated."""
        async with SkillsAPIClient() as client:
            return [
                r.model_dump(exclude_none=True)
                for r in await client.search_skills(
                    query, limit, skill_type, version=version
                )
            ]

    @mcp.tool(tags={"skills"}, annotations=READ_ONLY)
    async def get_skill_details(
        skill_id: Text, version: Text = "latest"
    ) -> dict[str, Any]:
        """Get a skill by its Lightcast ID."""
        async with SkillsAPIClient() as client:
            return (await client.get_skill_by_id(skill_id, version)).model_dump(
                exclude_none=True
            )

    @mcp.tool(tags={"skills"}, annotations=READ_ONLY)
    async def bulk_retrieve_skills(
        skill_ids: IDs, version: Text = "latest"
    ) -> list[dict[str, Any]]:
        """Retrieve multiple skills in one request."""
        async with SkillsAPIClient() as client:
            return [
                r.model_dump(exclude_none=True)
                for r in await client.bulk_retrieve_skills(skill_ids, version)
            ]

    @mcp.tool(tags={"skills"}, annotations=READ_ONLY)
    async def extract_skills_from_text(
        text: Text, confidence_threshold: Confidence = 0.5, version: Text = "latest"
    ) -> list[dict[str, Any]]:
        """Extract explicitly mentioned skills from text. Requires extraction permission and may consume a limited quota."""
        async with SkillsAPIClient() as client:
            return await client.extract_skills_from_text(
                text, confidence_threshold, version
            )

    @mcp.tool(tags={"skills"}, annotations=READ_ONLY)
    async def get_related_skills(
        skill_id: Text, limit: Limit = 10, version: Text = "latest"
    ) -> list[dict[str, Any]]:
        """Find related skills using the Skills API. Results are related skills, not scored Similarity mappings."""
        async with SkillsAPIClient() as client:
            return [
                r.model_dump(exclude_none=True)
                for r in await client.get_related_skills(skill_id, limit, version)
            ]

    @mcp.tool(tags={"similarity"}, annotations=READ_ONLY)
    async def find_similar_skills(skill_id: Text, limit: Limit = 10) -> dict[str, Any]:
        """Find scored similar skills. Requires the separate Similarity API subscription."""
        async with SimilarityAPIClient() as client:
            return await client.query_model("skill", skill_id, limit)

    @mcp.tool(tags={"skills"}, annotations=READ_ONLY)
    async def get_skills_metadata(version: Text = "latest") -> dict[str, Any]:
        """Discover the Skills taxonomy version, supported fields, and skill types."""
        async with SkillsAPIClient() as client:
            return await client.get_skills_metadata(version)
