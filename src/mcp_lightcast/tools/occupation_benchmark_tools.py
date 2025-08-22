"""MCP tools for Lightcast Occupation Benchmark API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.occupation_benchmark import OccupationBenchmarkAPIClient


def register_occupation_benchmark_tools(mcp: FastMCP):
    """Register core occupation benchmark-related MCP tools."""

    @mcp.tool
    async def get_occupation_benchmark(
        occupation_id: str,
        metrics: list[str] | None = None,
        region: str | None = None,
        time_period: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get salary and employment benchmarks for a specific occupation.
        
        Args:
            occupation_id: Occupation ID (SOC code or EMSI ID)
            metrics: List of metrics to retrieve (e.g., ['median_salary', 'employment'])
            region: Geographic region for benchmarks (optional)
            time_period: Time period for data (optional)
            version: API version to use (default: "latest")
            
        Returns:
            Benchmark data including salary and employment statistics
        """
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_benchmark_data(occupation_id, metrics, region, version)