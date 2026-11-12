"""Model queries and premium API discovery."""

from typing import Any, Literal

from fastmcp import FastMCP

from ..apis.career_pathways import CareerPathwaysAPIClient
from ..apis.occupation_benchmark import OccupationBenchmarkAPIClient
from ..apis.similarity import SimilarityAPIClient
from .types import READ_ONLY, Confidence, Limit, Text


def register_similarity_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"similarity"}, annotations=READ_ONLY)
    async def get_similarity_metadata() -> dict[str, Any]:
        """Discover Similarity models and the taxonomy versions they accept."""
        async with SimilarityAPIClient() as client:
            return await client.get_api_metadata()

    @mcp.tool(tags={"similarity"}, annotations=READ_ONLY)
    async def query_similarity(
        model: Text,
        input: str | list[str],
        limit: Limit = 10,
        min_score: Confidence = 0.5,
        filter_ids: list[str] | None = None,
        lot_version: Literal["6", "7"] = "7",
    ) -> dict[str, Any]:
        """Query a Similarity model, e.g. soc, skill, lotspecocc-skill, or skill-lotocc. Only skill-input models accept a list. Preserves upstream warnings."""
        async with SimilarityAPIClient() as client:
            return await client.query_model(
                model, input, limit, min_score, filter_ids, lot_version
            )

    @mcp.tool(tags={"benchmarks"}, annotations=READ_ONLY)
    async def get_benchmark_metadata() -> dict[str, Any]:
        """Discover benchmark dimensions, available datasets, regions, and taxonomy versions."""
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_api_metadata()

    @mcp.tool(tags={"pathways"}, annotations=READ_ONLY)
    async def get_pathways_metadata() -> dict[str, Any]:
        """Discover career-pathway dimensions, categories, nations, and taxonomy versions."""
        async with CareerPathwaysAPIClient() as client:
            return await client.get_api_metadata()

    @mcp.tool(tags={"pathways"}, annotations=READ_ONLY)
    async def get_career_next_steps(
        occupation_id: Text,
        dimension: Literal["soc", "onet", "lotocc", "lotspecocc"] = "lotspecocc",
        limit: Limit = 10,
        nation: Text = "us",
        categories: list[str] | None = None,
        lot_version: Literal["6", "7"] = "7",
    ) -> dict[str, Any]:
        """Find potential next occupations from the Career Pathways model. Discover available categories in metadata."""
        async with CareerPathwaysAPIClient() as client:
            return await client.get_next_steps(
                occupation_id, dimension, limit, nation, categories, lot_version
            )

    @mcp.tool(tags={"pathways"}, annotations=READ_ONLY)
    async def get_career_skill_gap(
        source_id: Text,
        destination_id: Text,
        dimension: Literal["soc", "onet", "lotocc", "lotspecocc"] = "lotspecocc",
        limit: Limit = 20,
        nation: Text = "us",
        lot_version: Literal["6", "7"] = "7",
    ) -> dict[str, Any]:
        """Compare source and destination occupations within the same taxonomy to identify skill gaps."""
        async with CareerPathwaysAPIClient() as client:
            return await client.get_skill_gap(
                source_id, destination_id, dimension, limit, nation, lot_version
            )
