"""Metadata-led, bounded access to licensed Core LMI datasets."""

from fastmcp import FastMCP

from ..apis.core_lmi import (
    CoreLmiAPIClient,
    CoreLmiQuery,
    DatasetCatalog,
    DatasetMetadata,
    DatasetVersions,
    DimensionResult,
    Offset,
    PageLimit,
    QueryResult,
)
from .types import READ_ONLY, Text


def register_core_lmi_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"core_lmi"}, annotations=READ_ONLY)
    async def list_core_lmi_datasets(
        query: str = "",
        include_definitions: bool = False,
        limit: PageLimit = 20,
        offset: Offset = 0,
    ) -> DatasetCatalog:
        """Discover Core LMI datasets and releases accessible to your account (agnitio scope). Optionally include descriptions and filter by name/text. Follow pagination.next_offset; metadata pagination is local after one upstream fetch."""
        async with CoreLmiAPIClient() as client:
            return await client.list_datasets(query, include_definitions, limit, offset)

    @mcp.tool(tags={"core_lmi"}, annotations=READ_ONLY)
    async def get_core_lmi_versions(dataset: Text) -> DatasetVersions:
        """List releases for an accessible Core LMI dataset. latest_numeric is discovered numerically, never taken from array order. Pin a returned release for reproducible queries; base/example require explicit selection."""
        async with CoreLmiAPIClient() as client:
            return await client.get_versions(dataset)

    @mcp.tool(tags={"core_lmi"}, annotations=READ_ONLY)
    async def get_core_lmi_metadata(
        dataset: Text,
        version: Text = "latest",
        metric_query: str = "",
        limit: PageLimit = 50,
        offset: Offset = 0,
    ) -> DatasetMetadata:
        """Inspect a Core LMI release's attributes, dimensions and available metrics before querying. Filter metrics by substring (e.g. Jobs. or Earnings); follow metrics_pagination.next_offset. Release version is different from metric year."""
        async with CoreLmiAPIClient() as client:
            return await client.get_metadata(
                dataset, version, metric_query, limit, offset
            )

    @mcp.tool(tags={"core_lmi"}, annotations=READ_ONLY)
    async def get_core_lmi_dimension(
        dataset: Text,
        dimension: Text,
        version: Text = "latest",
        search: Text | None = None,
        level: Text | None = None,
        aggregation_path: Text | None = None,
        limit: PageLimit = 50,
        offset: Offset = 0,
    ) -> DimensionResult:
        """Find valid dimension codes by name/code search, or browse a hierarchy using level and aggregation_path. Search and hierarchy filters are separate modes. Use returned child codes exactly, including leading zeros; metadata pagination is local."""
        async with CoreLmiAPIClient() as client:
            return await client.get_dimension(
                dataset,
                dimension,
                version,
                search,
                level,
                aggregation_path,
                limit,
                offset,
            )

    @mcp.tool(tags={"core_lmi"}, annotations=READ_ONLY)
    async def query_core_lmi(
        dataset: Text, query: CoreLmiQuery, version: Text = "latest"
    ) -> QueryResult:
        """Query employment, wages, education or other Core LMI measures using discovered metrics and dimension codes. Read-only POST; consumes quota. Supports named aggregations, mapLevel, LocationQuotient, ShiftShare, sorting and bounded pagination (100 rows default, 500 maximum per page, first 5000 rows accessible). data is column-oriented: combine values at matching row indices. Preserve returned version and upstream metadata; missing/suppressed values are not zero. Use sortBy for repeatable pages. Offset is applied locally to a bounded prefix because the service ignores native offset. Follow pagination.next_offset; narrow the query if has_more is true at window_limit. totalRows is upstream metadata, not a grand total."""
        async with CoreLmiAPIClient() as client:
            return await client.query(dataset, query, version)
