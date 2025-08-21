"""Lightcast Occupation Benchmark API client."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class BenchmarkMetric(BaseModel):
    """Benchmark metric model."""
    metric_name: str
    value: Union[float, int, str]
    percentile: Optional[float] = None
    benchmark_group: Optional[str] = None


class OccupationBenchmark(BaseModel):
    """Occupation benchmark result."""
    occupation_id: str
    occupation_title: str
    soc_code: Optional[str] = None
    metrics: List[BenchmarkMetric]
    benchmark_date: Optional[str] = None


class SalaryBenchmark(BaseModel):
    """Salary benchmark model."""
    occupation_id: str
    median_salary: float
    mean_salary: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    currency: str = "USD"
    region: Optional[str] = None


class SkillDemandBenchmark(BaseModel):
    """Skill demand benchmark model."""
    skill_id: str
    skill_name: str
    demand_score: float
    growth_rate: Optional[float] = None
    occupation_count: int
    job_posting_count: Optional[int] = None


class RegionalBenchmark(BaseModel):
    """Regional benchmark model."""
    region_id: str
    region_name: str
    metrics: List[BenchmarkMetric]
    comparison_to_national: Optional[Dict[str, float]] = None


class OccupationBenchmarkAPIClient(BaseLightcastClient):
    """Client for Lightcast Occupation Benchmark API."""
    
    def __init__(self):
        super().__init__(api_name="occupation_benchmark")
    
    # Working endpoints discovered from testing
    async def get_dimension_info(
        self,
        dimension: str
    ) -> Dict[str, Any]:
        """
        Get information about a specific dimension (taxonomy).
        
        Args:
            dimension: Dimension ID (lotocc, soc, onet, lotspecocc)
            
        Returns:
            Dimension information including title, description, and taxonomy versions
        """
        response = await self.get(f"dimensions/{dimension}")
        return response.get("data", {})
    
    async def get_lotocc_dimension(self) -> Dict[str, Any]:
        """Get LOT Occupation dimension information."""
        return await self.get_dimension_info("lotocc")
    
    async def get_soc_dimension(self) -> Dict[str, Any]:
        """Get SOC (Standard Occupation Classification) dimension information."""
        return await self.get_dimension_info("soc")
    
    async def get_onet_dimension(self) -> Dict[str, Any]:
        """Get O*NET dimension information."""
        return await self.get_dimension_info("onet")
    
    async def get_lotspecocc_dimension(self) -> Dict[str, Any]:
        """Get LOT Specialized Occupation dimension information."""
        return await self.get_dimension_info("lotspecocc")
    
    async def get_api_metadata(self) -> Dict[str, Any]:
        """
        Get comprehensive API metadata including available datasets and dimensions.
        
        Returns:
            API metadata with datasets, dimensions, regions, and taxonomy versions
        """
        response = await self.get("meta")
        return response.get("data", {})
    
    async def get_api_status(self) -> Dict[str, Any]:
        """
        Get API health status.
        
        Returns:
            API health status information
        """
        response = await self.get("status")
        return response.get("data", {})
    
    async def get_occupation_benchmark(
        self,
        occupation_id: str,
        metrics: Optional[List[str]] = None,
        region: Optional[str] = None,
        time_period: Optional[str] = None,
        version: str = "latest"
    ) -> OccupationBenchmark:
        """
        Get comprehensive benchmark data for an occupation.
        
        Args:
            occupation_id: Lightcast occupation ID
            metrics: Specific metrics to retrieve (salary, demand, growth, etc.)
            region: Geographic region for benchmarking
            time_period: Time period for benchmark (e.g., "2023", "2022-2023")
            version: API version to use
            
        Returns:
            Occupation benchmark data
        """
        params = {}
        if metrics:
            params["metrics"] = ",".join(metrics)
        if region:
            params["region"] = region
        if time_period:
            params["time_period"] = time_period
        
        response = await self.get(
            f"benchmark/versions/{version}/occupations/{occupation_id}",
            params=params,
            version=version
        )
        
        data = response.get("data", {})
        return OccupationBenchmark(
            occupation_id=occupation_id,
            occupation_title=data.get("title", ""),
            soc_code=data.get("soc_code"),
            metrics=[
                BenchmarkMetric(
                    metric_name=metric["name"],
                    value=metric["value"],
                    percentile=metric.get("percentile"),
                    benchmark_group=metric.get("group")
                )
                for metric in data.get("metrics", [])
            ],
            benchmark_date=data.get("benchmark_date")
        )
    
    async def get_salary_benchmarks(
        self,
        occupation_ids: List[str],
        region: Optional[str] = None,
        experience_level: Optional[str] = None,
        version: str = "latest"
    ) -> List[SalaryBenchmark]:
        """
        Get salary benchmark data for multiple occupations.
        
        Args:
            occupation_ids: List of occupation IDs
            region: Geographic region for salary data
            experience_level: Experience level filter (entry, mid, senior)
            version: API version to use
            
        Returns:
            List of salary benchmarks
        """
        data = {"occupation_ids": occupation_ids}
        if region:
            data["region"] = region
        if experience_level:
            data["experience_level"] = experience_level
        
        response = await self.post(
            f"benchmark/versions/{version}/salaries",
            data=data,
            version=version
        )
        
        result = []
        for item in response.get("data", []):
            salary_data = item.get("salary_data", {})
            result.append(SalaryBenchmark(
                occupation_id=item["occupation_id"],
                median_salary=salary_data.get("median", 0.0),
                mean_salary=salary_data.get("mean", 0.0),
                percentile_25=salary_data.get("p25", 0.0),
                percentile_75=salary_data.get("p75", 0.0),
                percentile_90=salary_data.get("p90", 0.0),
                currency=salary_data.get("currency", "USD"),
                region=item.get("region")
            ))
        
        return result
    
    async def get_skill_demand_benchmarks(
        self,
        skill_ids: Optional[List[str]] = None,
        occupation_filter: Optional[List[str]] = None,
        region: Optional[str] = None,
        time_period: Optional[str] = None,
        limit: int = 100,
        version: str = "latest"
    ) -> List[SkillDemandBenchmark]:
        """
        Get skill demand benchmark data.
        
        Args:
            skill_ids: Specific skill IDs to benchmark
            occupation_filter: Filter by occupation IDs
            region: Geographic region
            time_period: Time period for analysis
            limit: Maximum number of results
            version: API version to use
            
        Returns:
            List of skill demand benchmarks
        """
        params = {"limit": limit}
        if region:
            params["region"] = region
        if time_period:
            params["time_period"] = time_period
        
        data = {}
        if skill_ids:
            data["skill_ids"] = skill_ids
        if occupation_filter:
            data["occupation_filter"] = occupation_filter
        
        response = await self.post(
            f"benchmark/versions/{version}/skills/demand",
            data=data,
            params=params,
            version=version
        )
        
        result = []
        for item in response.get("data", []):
            result.append(SkillDemandBenchmark(
                skill_id=item["skill_id"],
                skill_name=item["skill_name"],
                demand_score=item.get("demand_score", 0.0),
                growth_rate=item.get("growth_rate"),
                occupation_count=item.get("occupation_count", 0),
                job_posting_count=item.get("job_posting_count")
            ))
        
        return result
    
    async def compare_occupations_benchmark(
        self,
        occupation_ids: List[str],
        metrics: List[str],
        region: Optional[str] = None,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Compare benchmark metrics across multiple occupations.
        
        Args:
            occupation_ids: List of occupation IDs to compare
            metrics: Benchmark metrics to compare
            region: Geographic region for comparison
            version: API version to use
            
        Returns:
            Occupation comparison data
        """
        data = {
            "occupation_ids": occupation_ids,
            "metrics": metrics
        }
        if region:
            data["region"] = region
        
        response = await self.post(
            f"benchmark/versions/{version}/occupations/compare",
            data=data,
            version=version
        )
        return response.get("data", {})
    
    async def get_regional_benchmarks(
        self,
        metric_type: str,
        regions: Optional[List[str]] = None,
        occupation_filter: Optional[List[str]] = None,
        version: str = "latest"
    ) -> List[RegionalBenchmark]:
        """
        Get regional benchmark data for specific metrics.
        
        Args:
            metric_type: Type of metric (salary, employment, growth, etc.)
            regions: Specific regions to include
            occupation_filter: Filter by occupation IDs
            version: API version to use
            
        Returns:
            List of regional benchmarks
        """
        params = {"metric_type": metric_type}
        if regions:
            params["regions"] = ",".join(regions)
        if occupation_filter:
            params["occupation_filter"] = ",".join(occupation_filter)
        
        response = await self.get(
            f"benchmark/versions/{version}/regions",
            params=params,
            version=version
        )
        
        result = []
        for item in response.get("data", []):
            result.append(RegionalBenchmark(
                region_id=item["region_id"],
                region_name=item["region_name"],
                metrics=[
                    BenchmarkMetric(
                        metric_name=metric["name"],
                        value=metric["value"],
                        percentile=metric.get("percentile"),
                        benchmark_group=metric.get("group")
                    )
                    for metric in item.get("metrics", [])
                ],
                comparison_to_national=item.get("national_comparison")
            ))
        
        return result
    
    async def get_employment_trends(
        self,
        occupation_id: str,
        years: Optional[List[int]] = None,
        region: Optional[str] = None,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Get employment trend data for an occupation.
        
        Args:
            occupation_id: Lightcast occupation ID
            years: Specific years to include in trend analysis
            region: Geographic region
            version: API version to use
            
        Returns:
            Employment trend data
        """
        params = {}
        if years:
            params["years"] = ",".join(map(str, years))
        if region:
            params["region"] = region
        
        response = await self.get(
            f"benchmark/versions/{version}/occupations/{occupation_id}/trends",
            params=params,
            version=version
        )
        return response.get("data", {})
    
    async def get_industry_benchmarks(
        self,
        industry_ids: List[str],
        metrics: List[str],
        region: Optional[str] = None,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Get benchmark data by industry.
        
        Args:
            industry_ids: List of industry IDs
            metrics: Benchmark metrics to retrieve
            region: Geographic region
            version: API version to use
            
        Returns:
            Industry benchmark data
        """
        data = {
            "industry_ids": industry_ids,
            "metrics": metrics
        }
        if region:
            data["region"] = region
        
        response = await self.post(
            f"benchmark/versions/{version}/industries",
            data=data,
            version=version
        )
        return response.get("data", {})
    
    async def get_benchmark_metadata(
        self,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Get Occupation Benchmark API metadata and version information.
        
        Args:
            version: API version to use
            
        Returns:
            API metadata and version information
        """
        response = await self.get(
            f"benchmark/versions/{version}",
            version=version
        )
        return response.get("data", {})