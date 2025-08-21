"""Lightcast Job Postings API client."""

from datetime import date
from typing import Any

from pydantic import BaseModel

from .base import BaseLightcastClient


class JobPosting(BaseModel):
    """Job posting model."""
    posting_id: str
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    posted_date: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = "USD"
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    industries: list[str] | None = None


class JobPostingStats(BaseModel):
    """Job posting statistics model."""
    total_postings: int
    unique_postings: int
    total_companies: int
    date_range: dict[str, str]
    top_locations: list[dict[str, Any]]
    top_companies: list[dict[str, Any]]


class SkillDemand(BaseModel):
    """Skill demand from job postings."""
    skill_id: str
    skill_name: str
    posting_count: int
    percentage_of_postings: float
    median_salary: float | None = None
    growth_rate: float | None = None


class SalaryInsights(BaseModel):
    """Salary insights from job postings."""
    occupation_id: str | None = None
    location: str | None = None
    median_salary: float
    mean_salary: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    sample_size: int
    currency: str = "USD"


class JobMarketTrends(BaseModel):
    """Job market trends model."""
    time_period: str
    total_postings: int
    growth_rate: float
    top_growing_skills: list[SkillDemand]
    top_declining_skills: list[SkillDemand]
    regional_insights: list[dict[str, Any]] | None = None


class JobPostingsAPIClient(BaseLightcastClient):
    """Client for Lightcast Job Postings API."""

    def __init__(self):
        super().__init__(api_name="job_postings")

    async def search_job_postings(
        self,
        query: str | None = None,
        occupation_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        location: str | None = None,
        company: str | None = None,
        date_from: str | date | None = None,
        date_to: str | date | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        employment_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Search job postings with various filters.
        
        Args:
            query: Free-text search query
            occupation_ids: Filter by occupation IDs
            skill_ids: Filter by required skills
            location: Geographic location filter
            company: Company name filter
            date_from: Start date for posting date range
            date_to: End date for posting date range
            salary_min: Minimum salary filter
            salary_max: Maximum salary filter
            employment_type: Employment type (full-time, part-time, contract)
            limit: Maximum number of results
            offset: Pagination offset
            version: API version to use
            
        Returns:
            Job postings search results
        """
        data = {
            "limit": limit,
            "offset": offset
        }

        if query:
            data["query"] = query
        if occupation_ids:
            data["occupation_ids"] = occupation_ids
        if skill_ids:
            data["skill_ids"] = skill_ids
        if location:
            data["location"] = location
        if company:
            data["company"] = company
        if date_from:
            data["date_from"] = str(date_from) if isinstance(date_from, date) else date_from
        if date_to:
            data["date_to"] = str(date_to) if isinstance(date_to, date) else date_to
        if salary_min:
            data["salary_min"] = salary_min
        if salary_max:
            data["salary_max"] = salary_max
        if employment_type:
            data["employment_type"] = employment_type

        response = await self.post(
            f"posting/versions/{version}/search",
            data=data,
            version=version
        )
        return response.get("data", {})

    async def get_job_posting_details(
        self,
        posting_id: str,
        include_skills: bool = True,
        include_company_info: bool = True,
        version: str = "latest"
    ) -> JobPosting:
        """
        Get detailed information for a specific job posting.
        
        Args:
            posting_id: Job posting ID
            include_skills: Include extracted skills
            include_company_info: Include company information
            version: API version to use
            
        Returns:
            Detailed job posting information
        """
        params = {}
        if include_skills:
            params["include_skills"] = "true"
        if include_company_info:
            params["include_company"] = "true"

        response = await self.get(
            f"posting/versions/{version}/postings/{posting_id}",
            params=params,
            version=version
        )

        data = response.get("data", {})
        return JobPosting(
            posting_id=posting_id,
            title=data.get("title", ""),
            company=data.get("company"),
            location=data.get("location"),
            description=data.get("description"),
            posted_date=data.get("posted_date"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            currency=data.get("currency", "USD"),
            employment_type=data.get("employment_type"),
            experience_level=data.get("experience_level"),
            skills=data.get("skills", []),
            industries=data.get("industries", [])
        )

    async def get_posting_statistics(
        self,
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        industry_ids: list[str] | None = None,
        date_from: str | date | None = None,
        date_to: str | date | None = None,
        version: str = "latest"
    ) -> JobPostingStats:
        """
        Get job posting statistics for specified filters.
        
        Args:
            occupation_ids: Filter by occupation IDs
            location: Geographic location filter
            industry_ids: Filter by industry IDs
            date_from: Start date for analysis
            date_to: End date for analysis
            version: API version to use
            
        Returns:
            Job posting statistics
        """
        data = {}
        if occupation_ids:
            data["occupation_ids"] = occupation_ids
        if location:
            data["location"] = location
        if industry_ids:
            data["industry_ids"] = industry_ids
        if date_from:
            data["date_from"] = str(date_from) if isinstance(date_from, date) else date_from
        if date_to:
            data["date_to"] = str(date_to) if isinstance(date_to, date) else date_to

        response = await self.post(
            f"posting/versions/{version}/statistics",
            data=data,
            version=version
        )

        stats_data = response.get("data", {})
        return JobPostingStats(
            total_postings=stats_data.get("total_postings", 0),
            unique_postings=stats_data.get("unique_postings", 0),
            total_companies=stats_data.get("total_companies", 0),
            date_range=stats_data.get("date_range", {}),
            top_locations=stats_data.get("top_locations", []),
            top_companies=stats_data.get("top_companies", [])
        )

    async def analyze_skill_demand(
        self,
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        time_period: str | None = None,
        skill_type: str | None = None,
        limit: int = 50,
        version: str = "latest"
    ) -> list[SkillDemand]:
        """
        Analyze skill demand from job postings.
        
        Args:
            occupation_ids: Filter by occupation IDs
            location: Geographic location filter
            time_period: Time period for analysis
            skill_type: Type of skills (technical, soft, specialized)
            limit: Maximum number of skills
            version: API version to use
            
        Returns:
            List of skill demand data
        """
        data = {"limit": limit}
        if occupation_ids:
            data["occupation_ids"] = occupation_ids
        if location:
            data["location"] = location
        if time_period:
            data["time_period"] = time_period
        if skill_type:
            data["skill_type"] = skill_type

        response = await self.post(
            f"posting/versions/{version}/skills/demand",
            data=data,
            version=version
        )

        skills = []
        for item in response.get("data", []):
            skills.append(SkillDemand(
                skill_id=item["skill_id"],
                skill_name=item["skill_name"],
                posting_count=item["posting_count"],
                percentage_of_postings=item["percentage"],
                median_salary=item.get("median_salary"),
                growth_rate=item.get("growth_rate")
            ))

        return skills

    async def get_salary_insights(
        self,
        occupation_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        time_period: str | None = None,
        version: str = "latest"
    ) -> list[SalaryInsights]:
        """
        Get salary insights from job postings.
        
        Args:
            occupation_ids: Filter by occupation IDs
            skill_ids: Filter by required skills
            location: Geographic location filter
            experience_level: Experience level filter
            time_period: Time period for analysis
            version: API version to use
            
        Returns:
            List of salary insights
        """
        data = {}
        if occupation_ids:
            data["occupation_ids"] = occupation_ids
        if skill_ids:
            data["skill_ids"] = skill_ids
        if location:
            data["location"] = location
        if experience_level:
            data["experience_level"] = experience_level
        if time_period:
            data["time_period"] = time_period

        response = await self.post(
            f"posting/versions/{version}/salaries",
            data=data,
            version=version
        )

        insights = []
        for item in response.get("data", []):
            insights.append(SalaryInsights(
                occupation_id=item.get("occupation_id"),
                location=item.get("location"),
                median_salary=item["median_salary"],
                mean_salary=item["mean_salary"],
                percentile_25=item["p25"],
                percentile_75=item["p75"],
                percentile_90=item["p90"],
                sample_size=item["sample_size"],
                currency=item.get("currency", "USD")
            ))

        return insights

    async def analyze_market_trends(
        self,
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        industry_ids: list[str] | None = None,
        time_periods: list[str] | None = None,
        version: str = "latest"
    ) -> JobMarketTrends:
        """
        Analyze job market trends from posting data.
        
        Args:
            occupation_ids: Filter by occupation IDs
            location: Geographic location filter
            industry_ids: Filter by industry IDs
            time_periods: Time periods for trend analysis
            version: API version to use
            
        Returns:
            Job market trends analysis
        """
        data = {}
        if occupation_ids:
            data["occupation_ids"] = occupation_ids
        if location:
            data["location"] = location
        if industry_ids:
            data["industry_ids"] = industry_ids
        if time_periods:
            data["time_periods"] = time_periods

        response = await self.post(
            f"posting/versions/{version}/trends",
            data=data,
            version=version
        )

        trends_data = response.get("data", {})

        # Parse growing skills
        growing_skills = []
        for skill_data in trends_data.get("growing_skills", []):
            growing_skills.append(SkillDemand(
                skill_id=skill_data["skill_id"],
                skill_name=skill_data["skill_name"],
                posting_count=skill_data["posting_count"],
                percentage_of_postings=skill_data["percentage"],
                median_salary=skill_data.get("median_salary"),
                growth_rate=skill_data.get("growth_rate")
            ))

        # Parse declining skills
        declining_skills = []
        for skill_data in trends_data.get("declining_skills", []):
            declining_skills.append(SkillDemand(
                skill_id=skill_data["skill_id"],
                skill_name=skill_data["skill_name"],
                posting_count=skill_data["posting_count"],
                percentage_of_postings=skill_data["percentage"],
                median_salary=skill_data.get("median_salary"),
                growth_rate=skill_data.get("growth_rate")
            ))

        return JobMarketTrends(
            time_period=trends_data.get("time_period", ""),
            total_postings=trends_data.get("total_postings", 0),
            growth_rate=trends_data.get("growth_rate", 0.0),
            top_growing_skills=growing_skills,
            top_declining_skills=declining_skills,
            regional_insights=trends_data.get("regional_insights")
        )

    async def get_company_insights(
        self,
        company_name: str,
        include_postings: bool = False,
        include_skills: bool = True,
        time_period: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get insights about a specific company's job postings.
        
        Args:
            company_name: Company name
            include_postings: Include sample job postings
            include_skills: Include skills analysis
            time_period: Time period for analysis
            version: API version to use
            
        Returns:
            Company insights data
        """
        params = {}
        if include_postings:
            params["include_postings"] = "true"
        if include_skills:
            params["include_skills"] = "true"
        if time_period:
            params["time_period"] = time_period

        response = await self.get(
            f"posting/versions/{version}/companies/{company_name}/insights",
            params=params,
            version=version
        )
        return response.get("data", {})

    async def extract_skills_from_posting(
        self,
        job_description: str,
        confidence_threshold: float = 0.7,
        include_soft_skills: bool = True,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Extract skills from a job posting description.
        
        Args:
            job_description: Job posting description text
            confidence_threshold: Minimum confidence for skill extraction
            include_soft_skills: Include soft skills in extraction
            version: API version to use
            
        Returns:
            List of extracted skills with confidence scores
        """
        data = {
            "description": job_description,
            "confidence_threshold": confidence_threshold,
            "include_soft_skills": include_soft_skills
        }

        response = await self.post(
            f"posting/versions/{version}/extract/skills",
            data=data,
            version=version
        )
        return response.get("data", [])

    async def get_postings_metadata(
        self,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Job Postings API metadata and version information.
        
        Args:
            version: API version to use
            
        Returns:
            API metadata and version information
        """
        response = await self.get(
            f"posting/versions/{version}",
            version=version
        )
        return response.get("data", {})

    async def get_postings_summary(
        self,
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        time_period: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get summary of job postings.
        """
        params = {}
        if occupation_ids:
            params["occupation_ids"] = ",".join(occupation_ids)
        if location:
            params["location"] = location
        if time_period:
            params["time_period"] = time_period

        response = await self.get(
            f"versions/{version}/summary",
            params=params,
            version=version
        )
        return response.get("data", {})

    async def get_top_skills(
        self,
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        limit: int = 20,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get top skills from job postings.
        """
        params = {"limit": limit}
        if occupation_ids:
            params["occupation_ids"] = ",".join(occupation_ids)
        if location:
            params["location"] = location

        response = await self.get(
            f"versions/{version}/skills",
            params=params,
            version=version
        )
        return response.get("data", [])

    async def get_available_facets(self) -> list[dict[str, Any]]:
        """
        Get available facets for job postings filtering.
        """
        response = await self.get("meta")
        facets_data = response.get("data", {})
        return facets_data.get("facets", [])
