"""MCP tools for Lightcast Titles API."""

from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

from src.mcp_lightcast.apis.titles import TitlesAPIClient


def register_titles_tools(mcp: FastMCP):
    """Register all titles-related MCP tools."""
    
    @mcp.tool
    async def search_job_titles(
        query: str,
        limit: int = 10,
        offset: int = 0,
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """
        Search for job titles in the Lightcast database.
        
        Args:
            query: Search term for job titles
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip (default: 0)
            version: API version to use (default: "2023.4")
            
        Returns:
            List of matching job titles with their IDs and metadata
        """
        async with TitlesAPIClient() as client:
            results = await client.search_titles(query, limit, offset, version)
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
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific job title.
        
        Args:
            title_id: Lightcast title ID
            version: API version to use (default: "2023.4")
            
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
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """
        Normalize a raw job title string to the best matching Lightcast title.
        
        Args:
            raw_title: Raw job title text to normalize
            version: API version to use (default: "2023.4")
            
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
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """
        Get the hierarchical structure for a job title.
        
        Args:
            title_id: Lightcast title ID
            version: API version to use (default: "2023.4")
            
        Returns:
            Hierarchical structure showing parent and child titles
        """
        async with TitlesAPIClient() as client:
            return await client.get_title_hierarchy(title_id, version)
    
    @mcp.tool
    async def get_titles_metadata(
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """
        Get metadata about the Lightcast titles taxonomy.
        
        Args:
            version: API version to use (default: "2023.4")
            
        Returns:
            Metadata about the titles database including statistics and version info
        """
        async with TitlesAPIClient() as client:
            return await client.get_titles_metadata(version)