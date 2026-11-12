"""MCP tools for the Titles taxonomy."""

from typing import Any

from fastmcp import FastMCP

from ..apis.titles import TitlesAPIClient
from .types import READ_ONLY, IDs, Limit, Text


def register_titles_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"titles"}, annotations=READ_ONLY)
    async def search_job_titles(
        query: Text, limit: Limit = 10, version: Text = "latest"
    ) -> list[dict[str, Any]]:
        """Search standardized job titles. version is a Titles taxonomy version or latest."""
        async with TitlesAPIClient() as client:
            return [
                r.model_dump(exclude_none=True)
                for r in await client.search_titles(query, limit, version)
            ]

    @mcp.tool(tags={"titles"}, annotations=READ_ONLY)
    async def get_job_title_details(
        title_id: Text, version: Text = "latest"
    ) -> dict[str, Any]:
        """Retrieve a standardized title by its Lightcast ID."""
        async with TitlesAPIClient() as client:
            return (await client.get_title_by_id(title_id, version)).model_dump(
                exclude_none=True
            )

    @mcp.tool(tags={"titles"}, annotations=READ_ONLY)
    async def bulk_retrieve_titles(
        title_ids: IDs, version: Text = "latest"
    ) -> list[dict[str, Any]]:
        """Retrieve multiple titles in one request."""
        async with TitlesAPIClient() as client:
            return [
                r.model_dump(exclude_none=True)
                for r in await client.bulk_retrieve_titles(title_ids, version)
            ]

    @mcp.tool(tags={"titles"}, annotations=READ_ONLY)
    async def normalize_job_title(
        title: Text, version: Text = "latest"
    ) -> dict[str, Any]:
        """Normalize a raw job title, with confidence. Requires normalization permission; may consume a limited quota."""
        async with TitlesAPIClient() as client:
            return await client.normalize_title(title, version)

    @mcp.tool(tags={"titles"}, annotations=READ_ONLY)
    async def get_titles_metadata(version: Text = "latest") -> dict[str, Any]:
        """Discover the current Titles taxonomy version and available fields."""
        async with TitlesAPIClient() as client:
            return await client.get_titles_metadata(version)
