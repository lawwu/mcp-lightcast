"""MCP tools for Lightcast Titles API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.titles import TitlesAPIClient


def register_titles_tools(mcp: FastMCP):
    """Register core titles-related MCP tools."""

    @mcp.tool
    async def search_job_titles(
        query: str,
        limit: int = 10,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Search for job titles in the Lightcast database.
        
        Args:
            query: Search term for job titles
            limit: Maximum number of results to return (default: 10)
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            List of matching job titles with their IDs and metadata
        """
        async with TitlesAPIClient() as client:
            results = await client.search_titles(query, limit, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type
                }
                for result in results
            ]

    @mcp.tool
    async def get_job_title_details(
        title_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific job title.
        
        Args:
            title_id: Lightcast title ID
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            Detailed title information including description and related occupations
        """
        async with TitlesAPIClient() as client:
            result = await client.get_title_by_id(title_id, version)
            return {
                "id": result.id,
                "name": result.name,
                "type": result.type,
                "pluralName": result.pluralName,
                "singularName": result.singularName
            }

    @mcp.tool
    async def bulk_retrieve_titles(
        title_ids: list[str],
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Retrieve multiple job titles by their IDs in a single efficient request.
        
        Args:
            title_ids: List of Lightcast title IDs to retrieve
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            List of detailed title information for all requested titles
        """
        async with TitlesAPIClient() as client:
            results = await client.bulk_retrieve_titles(title_ids, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type,
                    "pluralName": result.pluralName,
                    "singularName": result.singularName
                }
                for result in results
            ]

    @mcp.tool
    async def normalize_job_title(
        title: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Normalize a raw job title to match Lightcast's standardized titles.
        
        Args:
            title: Raw job title text to normalize
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            Normalized title information with confidence score and alternatives
        """
        async with TitlesAPIClient() as client:
            return await client.normalize_title(title, version)