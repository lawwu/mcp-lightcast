"""MCP tools for Lightcast Occupation Benchmark API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.occupation_benchmark import OccupationBenchmarkAPIClient


def register_occupation_benchmark_tools(mcp: FastMCP):
    """Register all occupation benchmark-related MCP tools."""

    @mcp.tool
    async def get_occupation_benchmark(
        occupation_id: str,
        metrics: list[str] | None = None,
        region: str | None = None,
        time_period: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get comprehensive benchmark data for an occupation.
        
        Args:
            occupation_id: Lightcast occupation ID
            metrics: Specific metrics to retrieve (salary, demand, growth, etc.)
            region: Geographic region for benchmarking
            time_period: Time period for benchmark (e.g., "2023", "2022-2023")
            version: API version to use (default: "latest")
            
        Returns:
            Occupation benchmark data
        """
        async with OccupationBenchmarkAPIClient() as client:
            result = await client.get_occupation_benchmark(occupation_id, metrics, region, time_period, version)
            return {
                "occupation_id": result.occupation_id,
                "occupation_title": result.occupation_title,
                "soc_code": result.soc_code,
                "metrics": [
                    {
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "percentile": metric.percentile,
                        "benchmark_group": metric.benchmark_group
                    }
                    for metric in result.metrics
                ],
                "benchmark_date": result.benchmark_date
            }

    @mcp.tool
    async def get_salary_benchmarks(
        occupation_ids: list[str],
        region: str | None = None,
        experience_level: str | None = None,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get salary benchmark data for multiple occupations.
        
        Args:
            occupation_ids: List of occupation IDs
            region: Geographic region for salary data
            experience_level: Experience level filter (entry, mid, senior)
            version: API version to use (default: "latest")
            
        Returns:
            List of salary benchmarks
        """
        async with OccupationBenchmarkAPIClient() as client:
            results = await client.get_salary_benchmarks(occupation_ids, region, experience_level, version)
            return [
                {
                    "occupation_id": result.occupation_id,
                    "median_salary": result.median_salary,
                    "mean_salary": result.mean_salary,
                    "percentile_25": result.percentile_25,
                    "percentile_75": result.percentile_75,
                    "percentile_90": result.percentile_90,
                    "currency": result.currency,
                    "region": result.region
                }
                for result in results
            ]

    @mcp.tool
    async def get_skill_demand_benchmarks(
        skill_ids: list[str] | None = None,
        occupation_filter: list[str] | None = None,
        region: str | None = None,
        time_period: str | None = None,
        limit: int = 100,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get skill demand benchmark data.
        
        Args:
            skill_ids: Specific skill IDs to benchmark
            occupation_filter: Filter by occupation IDs
            region: Geographic region
            time_period: Time period for analysis
            limit: Maximum number of results (default: 100)
            version: API version to use (default: "latest")
            
        Returns:
            List of skill demand benchmarks
        """
        async with OccupationBenchmarkAPIClient() as client:
            results = await client.get_skill_demand_benchmarks(skill_ids, occupation_filter, region, time_period, limit, version)
            return [
                {
                    "skill_id": result.skill_id,
                    "skill_name": result.skill_name,
                    "demand_score": result.demand_score,
                    "growth_rate": result.growth_rate,
                    "occupation_count": result.occupation_count,
                    "job_posting_count": result.job_posting_count
                }
                for result in results
            ]

    @mcp.tool
    async def compare_occupations_benchmark(
        occupation_ids: list[str],
        metrics: list[str],
        region: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Compare benchmark metrics across multiple occupations.
        
        Args:
            occupation_ids: List of occupation IDs to compare
            metrics: Benchmark metrics to compare
            region: Geographic region for comparison
            version: API version to use (default: "latest")
            
        Returns:
            Occupation comparison data
        """
        async with OccupationBenchmarkAPIClient() as client:
            return await client.compare_occupations_benchmark(occupation_ids, metrics, region, version)

    @mcp.tool
    async def get_regional_benchmarks(
        metric_type: str,
        regions: list[str] | None = None,
        occupation_filter: list[str] | None = None,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get regional benchmark data for specific metrics.
        
        Args:
            metric_type: Type of metric (salary, employment, growth, etc.)
            regions: Specific regions to include
            occupation_filter: Filter by occupation IDs
            version: API version to use (default: "latest")
            
        Returns:
            List of regional benchmarks
        """
        async with OccupationBenchmarkAPIClient() as client:
            results = await client.get_regional_benchmarks(metric_type, regions, occupation_filter, version)
            return [
                {
                    "region_id": result.region_id,
                    "region_name": result.region_name,
                    "metrics": [
                        {
                            "metric_name": metric.metric_name,
                            "value": metric.value,
                            "percentile": metric.percentile,
                            "benchmark_group": metric.benchmark_group
                        }
                        for metric in result.metrics
                    ],
                    "comparison_to_national": result.comparison_to_national
                }
                for result in results
            ]

    @mcp.tool
    async def get_employment_trends(
        occupation_id: str,
        years: list[int] | None = None,
        region: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get employment trend data for an occupation.
        
        Args:
            occupation_id: Lightcast occupation ID
            years: Specific years to include in trend analysis
            region: Geographic region
            version: API version to use (default: "latest")
            
        Returns:
            Employment trend data
        """
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_employment_trends(occupation_id, years, region, version)

    @mcp.tool
    async def get_industry_benchmarks(
        industry_ids: list[str],
        metrics: list[str],
        region: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get benchmark data by industry.
        
        Args:
            industry_ids: List of industry IDs
            metrics: Benchmark metrics to retrieve
            region: Geographic region
            version: API version to use (default: "latest")
            
        Returns:
            Industry benchmark data
        """
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_industry_benchmarks(industry_ids, metrics, region, version)

    @mcp.tool
    async def get_benchmark_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Occupation Benchmark API metadata and version information.
        
        Args:
            version: API version to use (default: "latest")
            
        Returns:
            API metadata and version information
        """
        async with OccupationBenchmarkAPIClient() as client:
            return await client.get_benchmark_metadata(version)
