"""US job-postings queries using native Lightcast filters."""

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from ..apis.job_postings import JobPostingsAPIClient, PostingFilters
from .types import READ_ONLY, Limit, Text


def register_job_postings_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"postings"}, annotations=READ_ONLY)
    async def search_job_postings(
        filters: PostingFilters,
        limit: Annotated[int, Field(ge=1, le=10)] = 10,
        page: Annotated[int, Field(ge=1)] = 1,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search US postings with native filters including required when (active or a start/end range), e.g. {"when": "active", "title": ["ET6850661D6AE5FA86"], "city_name": ["Seattle, WA"]}. Use metadata to discover filters; requires postings:us."""
        async with JobPostingsAPIClient() as client:
            return await client.search_postings(
                filters.model_dump(exclude_unset=True), limit, page, fields
            )

    @mcp.tool(tags={"postings"}, annotations=READ_ONLY)
    async def get_job_posting_details(posting_id: Text) -> dict[str, Any]:
        """Retrieve a US posting by ID. Requires posting-detail permissions."""
        async with JobPostingsAPIClient() as client:
            return await client.get_posting_details(posting_id)

    @mcp.tool(tags={"postings"}, annotations=READ_ONLY)
    async def get_posting_statistics(
        filters: PostingFilters, metrics: list[str] | None = None
    ) -> dict[str, Any]:
        """Get US posting totals; metrics default to unique_postings. filters.when is required. Discover filters and metrics in metadata."""
        async with JobPostingsAPIClient() as client:
            return await client.get_postings_summary(
                filters.model_dump(exclude_unset=True), metrics
            )

    @mcp.tool(tags={"postings"}, annotations=READ_ONLY)
    async def get_posting_rankings(
        facet: Text, filters: PostingFilters, limit: Limit = 10
    ) -> dict[str, Any]:
        """Rank a facet such as skills_name or company_name by unique US postings. filters.when is required."""
        async with JobPostingsAPIClient() as client:
            return await client.get_rankings(
                facet, filters.model_dump(exclude_unset=True), limit
            )

    @mcp.tool(tags={"postings"}, annotations=READ_ONLY)
    async def get_postings_metadata() -> dict[str, Any]:
        """Discover accessible US posting fields, filters, metrics, and available months."""
        async with JobPostingsAPIClient() as client:
            return await client.get_postings_metadata()
