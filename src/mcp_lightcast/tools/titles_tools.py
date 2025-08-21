"""MCP tools for Lightcast Titles API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.titles import TitlesAPIClient


def register_titles_tools(mcp: FastMCP):
    """Register all titles-related MCP tools."""

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
            Detailed title information including hierarchy and metadata
        """
        async with TitlesAPIClient() as client:
            result = await client.get_title_by_id(title_id, version)
            return {
                "id": result.id,
                "name": result.name,
                "type": result.type,
                "parent": result.parent,
                "children": result.children
            }

    @mcp.tool
    async def normalize_job_title(
        raw_title: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Normalize a raw job title string to the best matching Lightcast title.
        
        Args:
            raw_title: Raw job title text to normalize
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            Normalized title with confidence score and metadata
        """
        async with TitlesAPIClient() as client:
            result = await client.normalize_title(raw_title, version)
            return {
                "normalized_title": {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type,
                    "confidence": result.confidence
                },
                "original_title": raw_title
            }

    @mcp.tool
    async def get_title_hierarchy(
        title_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get the hierarchical structure for a job title.
        
        Args:
            title_id: Lightcast title ID
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            Hierarchical structure showing parent and child titles
        """
        async with TitlesAPIClient() as client:
            return await client.get_title_hierarchy(title_id, version)

    @mcp.tool
    async def get_titles_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get metadata about the Lightcast titles taxonomy.
        
        Args:
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            Metadata about the titles database including statistics and version info
        """
        async with TitlesAPIClient() as client:
            return await client.get_titles_metadata(version)

    @mcp.tool
    async def get_titles_version_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get comprehensive metadata about a specific titles API version.
        
        Args:
            version: API version to use (default: "latest", can specify previous versions like "5.47", "5.46", etc.)
            
        Returns:
            Comprehensive version metadata including field definitions and counts
        """
        async with TitlesAPIClient() as client:
            result = await client.get_version_metadata(version)
            return {
                "version": result.version,
                "title_count": result.titleCount,
                "removed_title_count": result.removedTitleCount,
                "fields": result.fields
            }

    @mcp.tool
    async def get_titles_general_metadata() -> dict[str, Any]:
        """
        Get general metadata about the titles taxonomy.
        
        Returns:
            General metadata including attribution and latest version information
        """
        async with TitlesAPIClient() as client:
            result = await client.get_general_metadata()
            return {
                "latest_version": result.latestVersion,
                "attribution": result.attribution
            }

    @mcp.tool
    async def bulk_retrieve_titles(
        title_ids: list[str],
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Retrieve multiple titles by their IDs in a single efficient request.
        
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
                    "parent": result.parent,
                    "children": result.children
                }
                for result in results
            ]
