"""MCP tools for Lightcast Similarity API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.similarity import SimilarityAPIClient
from ..apis.occupation_benchmark import OccupationBenchmarkAPIClient
from ..apis.career_pathways import CareerPathwaysAPIClient


def register_similarity_tools(mcp: FastMCP):
    """Register core similarity and premium API metadata tools."""

    @mcp.tool
    async def get_similarity_metadata() -> dict[str, Any]:
        """
        Get Similarity API metadata and capabilities.
        
        Returns:
            Similarity API metadata and available models
        """
        async with SimilarityAPIClient() as client:
            return await client.get_api_metadata()

    @mcp.tool
    async def get_benchmark_metadata() -> dict[str, Any]:
        """
        Get Occupation Benchmark API metadata and capabilities.
        
        Returns:
            Benchmark API metadata and available metrics
        """
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_api_metadata()

    @mcp.tool
    async def get_pathways_metadata() -> dict[str, Any]:
        """
        Get Career Pathways API metadata and capabilities.
        
        Returns:
            Career Pathways API metadata and available dimensions
        """
        async with CareerPathwaysAPIClient() as client:
            return await client.get_api_metadata()