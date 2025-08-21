"""MCP tools for Lightcast Job Postings API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.job_postings import JobPostingsAPIClient


def register_job_postings_tools(mcp: FastMCP):
    """Register all job postings-related MCP tools."""

    @mcp.tool
    async def search_job_postings(
        query: str | None = None,
        occupation_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        location: str | None = None,
        company: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
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
            date_from: Start date for posting date range (YYYY-MM-DD)
            date_to: End date for posting date range (YYYY-MM-DD)
            salary_min: Minimum salary filter
            salary_max: Maximum salary filter
            employment_type: Employment type (full-time, part-time, contract)
            limit: Maximum number of results (default: 100)
            offset: Pagination offset (default: 0)
            version: API version to use (default: "latest")
            
        Returns:
            Job postings search results
        """
        async with JobPostingsAPIClient() as client:
            return await client.search_job_postings(
                query, occupation_ids, skill_ids, location, company,
                date_from, date_to, salary_min, salary_max, employment_type,
                limit, offset, version
            )

    @mcp.tool
    async def get_job_posting_details(
        posting_id: str,
        include_skills: bool = True,
        include_company_info: bool = True,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get detailed information for a specific job posting.
        
        Args:
            posting_id: Job posting ID
            include_skills: Include extracted skills (default: True)
            include_company_info: Include company information (default: True)
            version: API version to use (default: "latest")
            
        Returns:
            Detailed job posting information
        """
        async with JobPostingsAPIClient() as client:
            result = await client.get_job_posting_details(posting_id, include_skills, include_company_info, version)
            return {
                "posting_id": result.posting_id,
                "title": result.title,
                "company": result.company,
                "location": result.location,
                "description": result.description,
                "posted_date": result.posted_date,
                "salary_min": result.salary_min,
                "salary_max": result.salary_max,
                "currency": result.currency,
                "employment_type": result.employment_type,
                "experience_level": result.experience_level,
                "skills": result.skills,
                "industries": result.industries
            }

    @mcp.tool
    async def get_posting_statistics(
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        industry_ids: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get job posting statistics for specified filters.
        
        Args:
            occupation_ids: Filter by occupation IDs
            location: Geographic location filter
            industry_ids: Filter by industry IDs
            date_from: Start date for analysis (YYYY-MM-DD)
            date_to: End date for analysis (YYYY-MM-DD)
            version: API version to use (default: "latest")
            
        Returns:
            Job posting statistics
        """
        async with JobPostingsAPIClient() as client:
            result = await client.get_posting_statistics(occupation_ids, location, industry_ids, date_from, date_to, version)
            return {
                "total_postings": result.total_postings,
                "unique_postings": result.unique_postings,
                "total_companies": result.total_companies,
                "date_range": result.date_range,
                "top_locations": result.top_locations,
                "top_companies": result.top_companies
            }

    @mcp.tool
    async def analyze_skill_demand(
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        time_period: str | None = None,
        skill_type: str | None = None,
        limit: int = 50,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Analyze skill demand from job postings.
        
        Args:
            occupation_ids: Filter by occupation IDs
            location: Geographic location filter
            time_period: Time period for analysis
            skill_type: Type of skills (technical, soft, specialized)
            limit: Maximum number of skills (default: 50)
            version: API version to use (default: "latest")
            
        Returns:
            List of skill demand data
        """
        async with JobPostingsAPIClient() as client:
            results = await client.analyze_skill_demand(occupation_ids, location, time_period, skill_type, limit, version)
            return [
                {
                    "skill_id": result.skill_id,
                    "skill_name": result.skill_name,
                    "posting_count": result.posting_count,
                    "percentage_of_postings": result.percentage_of_postings,
                    "median_salary": result.median_salary,
                    "growth_rate": result.growth_rate
                }
                for result in results
            ]

    @mcp.tool
    async def get_salary_insights(
        occupation_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        time_period: str | None = None,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get salary insights from job postings.
        
        Args:
            occupation_ids: Filter by occupation IDs
            skill_ids: Filter by required skills
            location: Geographic location filter
            experience_level: Experience level filter
            time_period: Time period for analysis
            version: API version to use (default: "latest")
            
        Returns:
            List of salary insights
        """
        async with JobPostingsAPIClient() as client:
            results = await client.get_salary_insights(occupation_ids, skill_ids, location, experience_level, time_period, version)
            return [
                {
                    "occupation_id": result.occupation_id,
                    "location": result.location,
                    "median_salary": result.median_salary,
                    "mean_salary": result.mean_salary,
                    "percentile_25": result.percentile_25,
                    "percentile_75": result.percentile_75,
                    "percentile_90": result.percentile_90,
                    "sample_size": result.sample_size,
                    "currency": result.currency
                }
                for result in results
            ]

    @mcp.tool
    async def analyze_market_trends(
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        industry_ids: list[str] | None = None,
        time_periods: list[str] | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Analyze job market trends from posting data.
        
        Args:
            occupation_ids: Filter by occupation IDs
            location: Geographic location filter
            industry_ids: Filter by industry IDs
            time_periods: Time periods for trend analysis
            version: API version to use (default: "latest")
            
        Returns:
            Job market trends analysis
        """
        async with JobPostingsAPIClient() as client:
            result = await client.analyze_market_trends(occupation_ids, location, industry_ids, time_periods, version)
            return {
                "time_period": result.time_period,
                "total_postings": result.total_postings,
                "growth_rate": result.growth_rate,
                "top_growing_skills": [
                    {
                        "skill_id": skill.skill_id,
                        "skill_name": skill.skill_name,
                        "posting_count": skill.posting_count,
                        "percentage_of_postings": skill.percentage_of_postings,
                        "median_salary": skill.median_salary,
                        "growth_rate": skill.growth_rate
                    }
                    for skill in result.top_growing_skills
                ],
                "top_declining_skills": [
                    {
                        "skill_id": skill.skill_id,
                        "skill_name": skill.skill_name,
                        "posting_count": skill.posting_count,
                        "percentage_of_postings": skill.percentage_of_postings,
                        "median_salary": skill.median_salary,
                        "growth_rate": skill.growth_rate
                    }
                    for skill in result.top_declining_skills
                ],
                "regional_insights": result.regional_insights
            }

    @mcp.tool
    async def get_company_insights(
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
            include_postings: Include sample job postings (default: False)
            include_skills: Include skills analysis (default: True)
            time_period: Time period for analysis
            version: API version to use (default: "latest")
            
        Returns:
            Company insights data
        """
        async with JobPostingsAPIClient() as client:
            return await client.get_company_insights(company_name, include_postings, include_skills, time_period, version)

    @mcp.tool
    async def extract_skills_from_posting(
        job_description: str,
        confidence_threshold: float = 0.7,
        include_soft_skills: bool = True,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Extract skills from a job posting description.
        
        Args:
            job_description: Job posting description text
            confidence_threshold: Minimum confidence for skill extraction (default: 0.7)
            include_soft_skills: Include soft skills in extraction (default: True)
            version: API version to use (default: "latest")
            
        Returns:
            List of extracted skills with confidence scores
        """
        async with JobPostingsAPIClient() as client:
            return await client.extract_skills_from_posting(job_description, confidence_threshold, include_soft_skills, version)

    @mcp.tool
    async def get_postings_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Job Postings API metadata and version information.
        
        Args:
            version: API version to use (default: "latest")
            
        Returns:
            API metadata and version information
        """
        async with JobPostingsAPIClient() as client:
            return await client.get_postings_metadata(version)
