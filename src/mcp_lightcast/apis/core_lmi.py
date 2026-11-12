"""Core LMI (Agnitio): discover versioned datasets, then query their native schema."""

import re
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import APIError, BaseLightcastClient, segment

Name = Annotated[str, Field(min_length=1)]
PageLimit = Annotated[int, Field(ge=1, le=500)]
Offset = Annotated[int, Field(ge=0)]
MAX_QUERY_WINDOW = 5000


class QueryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MetricOperation(QueryModel):
    name: Literal["LocationQuotient", "ShiftShare"]
    geoparent: Name
    along: Name
    base: Name | None = None

    @model_validator(mode="after")
    def require_shift_share_base(self) -> Self:
        if self.name == "ShiftShare" and self.base is None:
            raise ValueError("ShiftShare requires a base metric, such as Jobs.2020.")
        return self


class Metric(QueryModel):
    name: Name = Field(
        description="Exact metric from dataset metadata, e.g. Jobs.2025."
    )
    alias: Name | None = Field(default=None, alias="as")
    operation: MetricOperation | None = None


class MapLevel(QueryModel):
    level: Annotated[int, Field(ge=0)]
    predicate: Annotated[list[int], Field(min_length=1, max_length=1000)]


class Constraint(QueryModel):
    dimension_name: Name = Field(alias="dimensionName")
    as_identity: bool | None = Field(default=None, alias="asIdentity")
    map: (
        dict[Name, Annotated[list[Name], Field(min_length=1, max_length=1000)]] | None
    ) = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Output labels mapped to dimension codes. Use codes returned by dimension discovery.",
    )
    map_level: MapLevel | None = Field(default=None, alias="mapLevel")

    @model_validator(mode="after")
    def require_mapping(self) -> Self:
        if self.map is None and self.map_level is None and not self.as_identity:
            raise ValueError("A constraint needs map, mapLevel, or asIdentity=true.")
        return self


class SortKey(QueryModel):
    name: Name
    direction: Literal["ascending", "descending"] = "ascending"


class CoreLmiQuery(QueryModel):
    metrics: Annotated[list[Metric], Field(min_length=1, max_length=20)]
    constraints: Annotated[list[Constraint], Field(max_length=20)]
    sort_by: Annotated[list[SortKey], Field(max_length=20)] | None = Field(
        default=None, alias="sortBy"
    )
    offset: Offset = 0
    limit: PageLimit = 100

    @model_validator(mode="after")
    def unique_dimensions(self) -> Self:
        names = [item.dimension_name for item in self.constraints]
        if len(names) != len(set(names)):
            raise ValueError("Each dimension can appear only once in constraints.")
        if self.offset + self.limit > MAX_QUERY_WINDOW:
            raise ValueError(
                "offset + limit must be at most 5000; narrow the query to continue."
            )
        if self.offset and not self.sort_by:
            raise ValueError(
                "Supply sortBy when using a nonzero offset for consistent pages."
            )
        return self


class Page(BaseModel):
    offset: int
    limit: int
    returned: int
    total: int | None
    next_offset: int | None


def page(total: int, offset: int, limit: int, returned: int) -> Page:
    end = offset + returned
    return Page(
        offset=offset,
        limit=limit,
        returned=returned,
        total=total,
        next_offset=end if returned and end < total else None,
    )


class DatasetCatalog(BaseModel):
    datasets: list[dict[str, Any]]
    pagination: Page


class DatasetVersions(BaseModel):
    dataset: str
    versions: list[str]
    latest_numeric: str | None


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    datasetName: str
    versionName: str
    attributes: dict[str, Any]
    dimensions: list[dict[str, Any]]
    metrics: list[dict[str, Any]]
    metrics_pagination: Page


class DimensionResult(BaseModel):
    dataset: str
    version: str
    dimension: str
    items: list[dict[str, Any]]
    pagination: Page


class Column(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    type: str
    rows: list[Any]


class QueryPage(Page):
    fetched: int
    has_more: bool
    window_limit: int = MAX_QUERY_WINDOW


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    dataset: str
    version: str
    data: list[Column]
    errors: list[Any]
    timings: list[str]
    totalRows: int
    pagination: QueryPage


def latest_numeric(versions: list[str]) -> str | None:
    candidates = [v for v in versions if re.fullmatch(r"\d+(?:\.\d+)*", v)]
    return max(candidates, key=lambda v: tuple(map(int, v.split("."))), default=None)


class CoreLmiAPIClient(BaseLightcastClient):
    def __init__(self) -> None:
        super().__init__("core_lmi")

    async def list_datasets(
        self,
        query: str = "",
        include_definitions: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> DatasetCatalog:
        result = await self.get("meta/definitions" if include_definitions else "meta")
        datasets = result.get("datasets")
        if not isinstance(datasets, list):
            raise APIError("Core LMI returned an invalid dataset catalog.")
        matches = [
            d
            for d in datasets
            if query.casefold()
            in " ".join(
                str(d.get(k, "")) for k in ("name", "title", "description")
            ).casefold()
        ]
        matches.sort(key=lambda d: d["name"].casefold())
        items = matches[offset : offset + limit]
        return DatasetCatalog(
            datasets=items, pagination=page(len(matches), offset, limit, len(items))
        )

    async def get_versions(self, dataset: str) -> DatasetVersions:
        result = await self._request_json("GET", f"meta/dataset/{segment(dataset)}")
        if not isinstance(result, list) or not all(isinstance(v, str) for v in result):
            raise APIError("Core LMI returned an invalid version list.")
        return DatasetVersions(
            dataset=dataset, versions=result, latest_numeric=latest_numeric(result)
        )

    async def resolve_version(self, dataset: str, version: str) -> str:
        if version != "latest":
            segment(version)
            return version
        versions = await self.get_versions(dataset)
        if versions.latest_numeric is None:
            raise APIError(
                "This Core LMI dataset has no numeric release. Use an explicit version from get_core_lmi_versions, such as base or example."
            )
        return versions.latest_numeric

    async def get_metadata(
        self,
        dataset: str,
        version: str = "latest",
        metric_query: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> DatasetMetadata:
        resolved = await self.resolve_version(dataset, version)
        result = await self.get(f"meta/dataset/{segment(dataset)}/{segment(resolved)}")
        metrics = result.get("metrics")
        if not isinstance(metrics, list):
            raise APIError("Core LMI returned invalid metric metadata.")
        matches = [
            m
            for m in metrics
            if metric_query.casefold() in str(m.get("name", "")).casefold()
        ]
        items = matches[offset : offset + limit]
        return DatasetMetadata.model_validate(
            {
                **result,
                "metrics": items,
                "metrics_pagination": page(len(matches), offset, limit, len(items)),
            }
        )

    async def get_dimension(
        self,
        dataset: str,
        dimension: str,
        version: str = "latest",
        search: str | None = None,
        level: str | None = None,
        aggregation_path: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DimensionResult:
        if search is not None and (level is not None or aggregation_path is not None):
            raise APIError(
                "Use either search or hierarchy filters (level/aggregation_path), in separate calls."
            )
        resolved = await self.resolve_version(dataset, version)
        endpoint = (
            f"meta/dataset/{segment(dataset)}/{segment(resolved)}/{segment(dimension)}"
        )
        if search is not None:
            items = await self._request_json(
                "GET", endpoint + f"/search/{segment(search)}"
            )
        else:
            params = {
                k: v
                for k, v in {"level": level, "aggpath": aggregation_path}.items()
                if v is not None
            }
            result = await self.get(endpoint, params=params)
            items = result.get("hierarchy")
        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            raise APIError("Core LMI returned an invalid dimension hierarchy.")
        selected = items[offset : offset + limit]
        return DimensionResult(
            dataset=dataset,
            version=resolved,
            dimension=dimension,
            items=selected,
            pagination=page(len(items), offset, limit, len(selected)),
        )

    async def query(
        self, dataset: str, query: CoreLmiQuery, version: str = "latest"
    ) -> QueryResult:
        resolved = await self.resolve_version(dataset, version)
        # The live Agnitio service ignores the documented offset parameter.
        # Fetch a bounded prefix plus one lookahead row, then slice locally.
        fetch_limit = query.offset + query.limit + 1
        body = query.model_dump(by_alias=True, exclude_none=True)
        body["offset"] = 0
        body["limit"] = fetch_limit
        result = await self.post(
            f"{segment(dataset)}/{segment(resolved)}",
            data=body,
        )
        if result.get("errors"):
            raise APIError(
                "Core LMI reported query errors. Check the dataset's exact metric names, dimension codes, and supported aggregations using metadata tools.",
                response_data=result,
            )
        columns = result.get("data")
        if not isinstance(columns, list) or not all(
            isinstance(c, dict) and isinstance(c.get("rows"), list) for c in columns
        ):
            raise APIError("Core LMI returned invalid data columns.")
        counts = {len(c["rows"]) for c in columns}
        if len(counts) > 1:
            raise APIError("Core LMI returned inconsistent column lengths.")
        fetched = next(iter(counts), 0)
        if fetched > fetch_limit:
            raise APIError(
                "Core LMI returned more rows than the requested retrieval limit."
            )
        end = query.offset + query.limit
        selected = [{**c, "rows": c["rows"][query.offset : end]} for c in columns]
        count = len(selected[0]["rows"]) if selected else 0
        has_more = fetched > end
        return QueryResult.model_validate(
            {
                **result,
                "dataset": dataset,
                "version": resolved,
                "data": selected,
                # Preserve upstream totalRows, but do not call it a grand total.
                "pagination": QueryPage(
                    offset=query.offset,
                    limit=query.limit,
                    returned=count,
                    total=None,
                    next_offset=end if has_more and end < MAX_QUERY_WINDOW else None,
                    fetched=fetched,
                    has_more=has_more,
                ),
            }
        )
