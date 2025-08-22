"""MCP tools for Lightcast Classification API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.classification import ClassificationAPIClient


def register_classification_tools(mcp: FastMCP):
    """Register core classification-related MCP tools."""

    @mcp.tool
    async def get_classification_metadata(
        version: str = "2025.8"
    ) -> dict[str, Any]:
        """
        Get Classification API metadata and capabilities.
        
        Args:
            version: API version to use (default: "2025.8")
            
        Returns:
            Classification API metadata and version information
        """
        async with ClassificationAPIClient() as client:
            return await client.get_version_metadata(version)