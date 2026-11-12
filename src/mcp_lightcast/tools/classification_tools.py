"""Discovery and current Classification operations."""

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from ..apis.classification import ClassificationAPIClient
from .types import READ_ONLY, Confidence, IDs, Text


def register_classification_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"classification"}, annotations=READ_ONLY)
    async def get_classification_metadata(version: Text = "latest") -> dict[str, Any]:
        """Get source types for an active classifier release. latest discovers the newest nonexpired release."""
        async with ClassificationAPIClient() as client:
            return await client.get_version_metadata(version)

    @mcp.tool(tags={"classification"}, annotations=READ_ONLY)
    async def list_classification_releases() -> list[dict[str, Any]]:
        """List classifier releases, removal dates, and supported taxonomy versions."""
        async with ClassificationAPIClient() as client:
            return await client.get_releases()

    @mcp.tool(tags={"classification"}, annotations=READ_ONLY)
    async def list_taxonomy_mappings() -> list[dict[str, Any]]:
        """Discover mapping names and source/destination taxonomy versions; do this before mapping IDs."""
        async with ClassificationAPIClient() as client:
            return await client.get_available_mappings()

    @mcp.tool(tags={"classification"}, annotations=READ_ONLY)
    async def map_taxonomy_concepts(mapping_name: Text, ids: IDs) -> dict[str, Any]:
        """Map concept IDs using a mapping name returned by list_taxonomy_mappings."""
        async with ClassificationAPIClient() as client:
            return await client.map_concepts(mapping_name, ids)

    @mcp.tool(tags={"classification"}, annotations=READ_ONLY)
    async def classify_occupation(
        title: Text,
        description: str = "",
        limit: Annotated[int, Field(ge=1, le=5)] = 5,
        confidence_threshold: Confidence = 0.5,
        version: Text = "latest",
    ) -> dict[str, Any]:
        """Classify a title and optional description to LOT specialized occupations. May consume a limited classifier quota."""
        async with ClassificationAPIClient() as client:
            return await client.classify_occupation(
                title, description, limit, confidence_threshold, version
            )
