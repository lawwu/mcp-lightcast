"""Occupation Benchmark tools."""

from typing import Any, Literal

from fastmcp import FastMCP

from ..apis.occupation_benchmark import OccupationBenchmarkAPIClient
from .types import READ_ONLY, Text


def register_occupation_benchmark_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"benchmarks"}, annotations=READ_ONLY)
    async def get_occupation_benchmark(
        occupation_id: Text,
        metrics: list[str] | None = None,
        region: dict[str, str] | None = None,
        dimension: Literal["lotocc", "lotspecocc"] = "lotocc",
        lot_version: Literal["6", "7"] = "7",
    ) -> dict[str, Any]:
        """Benchmark a LOT occupation. metrics are dataset names (salary, demand, specializedSkills, etc.); region is {"nation": "us"}. Preserves warnings about unavailable datasets."""
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_benchmark_data(
                occupation_id, metrics, region, dimension, lot_version
            )
