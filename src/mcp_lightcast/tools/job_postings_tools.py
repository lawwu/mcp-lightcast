"""MCP tools for Lightcast Job Postings API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.job_postings import JobPostingsAPIClient


def register_job_postings_tools(mcp: FastMCP):
    """Register core job postings-related MCP tools."""

    @mcp.tool
    async def search_job_postings(
        query: str | None = None,
        location: str | None = None,
        occupation_ids: list[str] | None = None,
        limit: int = 10,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Search job postings in real-time job market data.
        
        Args:
            query: Search term for job postings (optional)
            location: Geographic location filter (optional)
            occupation_ids: List of occupation IDs to filter by (optional)
            limit: Maximum number of results to return (default: 10)
            version: API version to use (default: "latest")
            
        Returns:
            List of job postings with their details
        """
        async with JobPostingsAPIClient() as client:
            return await client.search_postings(query, location, occupation_ids, limit, version)

    @mcp.tool
    async def get_job_posting_details(
        posting_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific job posting.
        
        Args:
            posting_id: Job posting ID
            version: API version to use (default: "latest")
            
        Returns:
            Detailed job posting information
        """
        async with JobPostingsAPIClient() as client:
            return await client.get_posting_details(posting_id, version)

    @mcp.tool
    async def get_posting_statistics(
        occupation_ids: list[str] | None = None,
        location: str | None = None,
        time_period: str = "30d",
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get job posting trends and analytics.
        
        Args:
            occupation_ids: List of occupation IDs to analyze (optional)
            location: Geographic location to analyze (optional)
            time_period: Time period for analysis (default: "30d")
            version: API version to use (default: "latest")
            
        Returns:
            Job posting statistics and trends
        """
        async with JobPostingsAPIClient() as client:
            return await client.get_postings_summary(occupation_ids, location, version)