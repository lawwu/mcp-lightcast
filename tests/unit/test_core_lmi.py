"""Core LMI HTTP contracts, pagination, query limits, and data integrity."""

import json

import pytest
from pydantic import ValidationError

from mcp_lightcast.apis.base import APIError, RateLimitError
from mcp_lightcast.apis.core_lmi import CoreLmiAPIClient, CoreLmiQuery


def native_result(rows=None, total=1):
    return {
        "data": [
            {"name": "Jobs", "type": "Double", "rows": [None] if rows is None else rows}
        ],
        "errors": [],
        "timings": ["Query: 1ms"],
        "totalRows": total,
    }


async def test_versions_are_arrays_and_latest_is_numeric(api_mock):
    api_mock.add_response(json=["2026.9", "base", "2026.10", "2025.4"])
    api_mock.add_response(json=native_result())
    async with CoreLmiAPIClient() as c:
        result = await c.query(
            "emsi.us.occupation",
            CoreLmiQuery(metrics=[{"name": "Jobs.2025"}], constraints=[]),
        )
    assert result.version == "2026.10"
    assert result.data[0].rows == [None]
    requests = api_mock.get_requests()
    assert requests[0].url.path == "/meta/dataset/emsi.us.occupation"
    assert requests[1].url.path == "/emsi.us.occupation/2026.10"
    assert requests[0].headers["Authorization"] == "Bearer test-agnitio-1"


async def test_pinned_query_serializes_native_aliases_and_pagination(api_mock):
    api_mock.add_response(json=native_result([1, 2, 10, 20, 30], total=5))
    body = {
        "metrics": [
            {
                "name": "Jobs.2025",
                "as": "Jobs",
                "operation": {
                    "name": "LocationQuotient",
                    "geoparent": "0",
                    "along": "Industry",
                },
            }
        ],
        "constraints": [
            {"dimensionName": "Area", "map": {"Example": ["00123"]}},
            {"dimensionName": "Industry", "mapLevel": {"level": 2, "predicate": [0]}},
        ],
        "sortBy": [{"name": "Jobs", "direction": "descending"}],
        "offset": 2,
        "limit": 2,
    }
    async with CoreLmiAPIClient() as c:
        result = await c.query(
            "emsi.us.industry", CoreLmiQuery.model_validate(body), "2026.4"
        )
    assert json.loads(api_mock.get_request().content) == {
        **body,
        "offset": 0,
        "limit": 5,
    }
    assert result.data[0].rows == [10, 20]
    assert result.pagination.next_offset == 4
    assert result.totalRows == 5
    assert result.timings == ["Query: 1ms"]


async def test_catalog_is_filtered_sorted_and_paginated(api_mock):
    api_mock.add_response(
        json={
            "datasets": [
                {"name": "b.occ", "title": "Occupation B"},
                {"name": "a.occ", "title": "Occupation A"},
                {"name": "x"},
            ]
        }
    )
    async with CoreLmiAPIClient() as c:
        result = await c.list_datasets("Occupation", include_definitions=True, limit=1)
    assert result.datasets == [{"name": "a.occ", "title": "Occupation A"}]
    assert result.pagination.next_offset == 1 and result.pagination.total == 2
    assert api_mock.get_request().url.path == "/meta/definitions"


async def test_metric_discovery_preserves_metadata_and_reports_remaining(api_mock):
    api_mock.add_response(
        json={
            "datasetName": "example",
            "versionName": "2026.4",
            "attributes": {"currentYear": "2025"},
            "dimensions": [{"name": "Area"}],
            "metrics": [
                {"name": "Jobs.2024"},
                {"name": "Other"},
                {"name": "Jobs.2025"},
            ],
            "warnings": ["example warning"],
        }
    )
    async with CoreLmiAPIClient() as c:
        result = await c.get_metadata(
            "example", "2026.4", metric_query="Jobs.", limit=1, offset=1
        )
    assert result.metrics == [{"name": "Jobs.2025"}]
    assert result.metrics_pagination.total == 2
    assert result.model_dump()["warnings"] == ["example warning"]


async def test_dimension_hierarchy_filters_and_search_path(api_mock):
    api_mock.add_response(
        json={
            "name": "Area",
            "hierarchy": [{"child": "01", "name": "A"}, {"child": "02", "name": "B"}],
        }
    )
    api_mock.add_response(json=[{"child": "00123", "name": "A/B"}])
    async with CoreLmiAPIClient() as c:
        hierarchy = await c.get_dimension(
            "example", "Area", "2026.4", level="2", aggregation_path="1", limit=1
        )
        searched = await c.get_dimension("example", "Area", "2026.4", search="A/B")
    assert hierarchy.pagination.next_offset == 1
    assert searched.items[0]["child"] == "00123"
    reqs = api_mock.get_requests()
    assert dict(reqs[0].url.params) == {"level": "2", "aggpath": "1"}
    assert reqs[1].url.raw_path.endswith(b"/search/A%2FB")


async def test_dimension_modes_are_exclusive_before_network():
    async with CoreLmiAPIClient() as c:
        with pytest.raises(APIError, match="either search"):
            await c.get_dimension("example", "Area", search="x", level="2")


async def test_special_version_requires_explicit_choice(api_mock):
    api_mock.add_response(json=["example", "base"])
    async with CoreLmiAPIClient() as c:
        with pytest.raises(APIError, match="explicit version"):
            await c.resolve_version("example", "latest")
        assert await c.resolve_version("example", "base") == "base"


@pytest.mark.parametrize(
    "change",
    [
        {"metrics": []},
        {"limit": 0},
        {"limit": 501},
        {"offset": -1},
        {"constraints": [{"dimensionName": "Area"}]},
        {"constraints": [{"dimensionName": "Area", "map": {"Empty": []}}]},
        {
            "constraints": [
                {"dimensionName": "Area", "map": {"A": ["1"]}},
                {"dimensionName": "Area", "asIdentity": True},
            ]
        },
        {
            "metrics": [
                {
                    "name": "Jobs.2025",
                    "operation": {
                        "name": "ShiftShare",
                        "geoparent": "0",
                        "along": "Industry",
                    },
                }
            ]
        },
        {"unrecognized": True},
    ],
)
def test_invalid_queries_are_rejected(change):
    with pytest.raises(ValidationError):
        CoreLmiQuery.model_validate(
            {"metrics": [{"name": "Jobs.2025"}], "constraints": [], **change}
        )


@pytest.mark.parametrize(
    "result, message",
    [
        ({**native_result(), "errors": ["private upstream details"]}, "query errors"),
        (
            {
                **native_result(),
                "data": [{"name": "A", "rows": [1]}, {"name": "B", "rows": []}],
            },
            "column lengths",
        ),
        (native_result([1, 2, 3]), "more rows"),
        ({**native_result(), "data": {}}, "invalid data"),
    ],
)
async def test_failed_or_malformed_query_never_reports_success(
    api_mock, result, message
):
    api_mock.add_response(json=result)
    async with CoreLmiAPIClient() as c:
        with pytest.raises(APIError, match=message) as exc:
            await c.query(
                "example",
                CoreLmiQuery(metrics=[{"name": "Jobs"}], constraints=[], limit=1),
                "base",
            )
    assert "private upstream details" not in str(exc.value)


async def test_agnitio_quota_headers_are_preserved_without_retry(api_mock):
    api_mock.add_response(
        status_code=429,
        headers={"X-Rate-Limit-Limit": "5m", "X-Rate-Limit-Remaining": "0"},
    )
    async with CoreLmiAPIClient() as c:
        with pytest.raises(RateLimitError) as exc:
            await c.get_versions("example")
    assert exc.value.response_data["remaining"] == "0"
    assert exc.value.response_data["limit"] == "5m"
    assert len(api_mock.get_requests()) == 1


async def test_core_lmi_root_override(monkeypatch):
    monkeypatch.setenv("LIGHTCAST_CORE_LMI_URL", "https://example.test/lmi/")
    async with CoreLmiAPIClient() as c:
        assert c.base_url == "https://example.test/lmi"
        assert c.required_scope == "agnitio"


async def test_lookahead_pagination_handles_ignored_upstream_offset(api_mock):
    api_mock.add_response(json=native_result([10, 20], total=2))
    api_mock.add_response(json=native_result([10, 20], total=2))
    async with CoreLmiAPIClient() as c:
        first = await c.query(
            "example",
            CoreLmiQuery(metrics=[{"name": "Jobs"}], constraints=[], limit=1),
            "base",
        )
        last = await c.query(
            "example",
            CoreLmiQuery(
                metrics=[{"name": "Jobs"}],
                constraints=[],
                limit=1,
                offset=1,
                sortBy=[{"name": "Jobs"}],
            ),
            "base",
        )
    assert first.totalRows == 2
    assert first.pagination.total is None and first.pagination.next_offset == 1
    assert first.data[0].rows == [10]
    assert last.data[0].rows == [20]
    assert last.pagination.next_offset is None and not last.pagination.has_more
    assert all(json.loads(r.content)["offset"] == 0 for r in api_mock.get_requests())


@pytest.mark.parametrize(
    "fields",
    [{"offset": 1}, {"offset": 4999, "limit": 2, "sortBy": [{"name": "Jobs"}]}],
)
def test_paging_requires_sorting_and_a_bounded_window(fields):
    with pytest.raises(ValidationError):
        CoreLmiQuery.model_validate(
            {"metrics": [{"name": "Jobs"}], "constraints": [], **fields}
        )


async def test_query_window_boundary_is_explicit(api_mock):
    api_mock.add_response(json=native_result(list(range(5001)), total=5001))
    async with CoreLmiAPIClient() as c:
        result = await c.query(
            "example",
            CoreLmiQuery(
                metrics=[{"name": "Jobs"}],
                constraints=[],
                sortBy=[{"name": "Jobs"}],
                offset=4999,
                limit=1,
            ),
            "base",
        )
    assert result.data[0].rows == [4999]
    assert result.pagination.has_more and result.pagination.next_offset is None
    assert result.pagination.window_limit == 5000


async def test_core_rate_spacing_is_shared_between_clients(
    monkeypatch, api_mock, clock
):
    monkeypatch.setenv("LIGHTCAST_CORE_LMI_REQUESTS_PER_SECOND", "1")
    api_mock.add_response(json={"datasets": []}, is_reusable=True)
    async with CoreLmiAPIClient() as first, CoreLmiAPIClient() as second:
        await first.list_datasets()
        await second.list_datasets()
    assert clock.delays == [0, 1]
