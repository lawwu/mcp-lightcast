"""Current and legacy MCP interoperability and HTTP request protections."""

import httpx
import jsonschema
import pytest
from fastmcp import Client

from mcp_lightcast.server import mcp


@pytest.mark.parametrize(
    "mode,version", [("auto", "2026-07-28"), ("legacy", "2025-11-25")]
)
async def test_both_protocol_eras_and_stable_catalog(mode, version):
    async with Client(mcp, mode=mode) as client:
        first = await client.list_tools()
        second = await client.list_tools()
        assert client.protocol_version == version
        assert client.server_info.version == "0.4.1"
        assert "Core LMI" in client.instructions
    assert [t.name for t in first] == [t.name for t in second]
    assert len(first) == 37
    assert all(
        t.annotations.read_only_hint and t.annotations.idempotent_hint for t in first
    )
    assert all(t.output_schema is not None for t in first)


async def test_structured_core_query_matches_advertised_output_schema(api_mock):
    api_mock.add_response(
        json={
            "data": [{"name": "Jobs", "type": "Double", "rows": [None]}],
            "errors": [],
            "timings": [],
            "totalRows": 1,
        }
    )
    async with Client(mcp) as client:
        tool = next(t for t in await client.list_tools() if t.name == "query_core_lmi")
        result = await client.call_tool(
            "query_core_lmi",
            {
                "dataset": "example",
                "version": "base",
                "query": {"metrics": [{"name": "Jobs"}], "constraints": []},
            },
        )
    jsonschema.validate(result.structured_content, tool.output_schema)
    assert result.structured_content["data"][0]["rows"] == [None]
    assert result.structured_content["version"] == "base"
    assert result.content  # Text fallback remains available to older clients.


async def test_actionable_errors_are_marked_and_do_not_expose_upstream_body(api_mock):
    api_mock.add_response(
        status_code=403, json={"message": "private licensed response and token"}
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_core_lmi_versions", {"dataset": "example"}, raise_on_error=False
        )
    assert result.is_error
    assert "HTTP 403" in result.content[0].text
    assert "scope" in result.content[0].text
    assert "private licensed" not in result.content[0].text


@pytest.mark.parametrize(
    "origin,host",
    [
        ("https://evil.example", "127.0.0.1"),
        ("null", "127.0.0.1"),
        ("http://127.0.0.1", "evil.example"),
    ],
)
async def test_http_rejects_untrusted_origin_or_host(origin, host):
    app = mcp.http_app(host_origin_protection=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
    ) as client:
        response = await client.post(
            "/mcp",
            headers={"Origin": origin, "Host": host},
            json={"jsonrpc": "2.0", "id": 1, "method": "server/discover"},
        )
    assert response.status_code in {403, 421}


@pytest.mark.parametrize(
    "name,args",
    [
        (
            "query_core_lmi",
            {
                "dataset": "example",
                "query": {
                    "metrics": [{"name": "Jobs"}],
                    "constraints": [],
                    "limit": 501,
                },
            },
        ),
        (
            "get_core_lmi_dimension",
            {"dataset": "example", "dimension": "Area", "offset": -1},
        ),
        ("list_core_lmi_datasets", {"limit": "10"}),
    ],
)
async def test_invalid_core_arguments_fail_before_network(name, args):
    async with Client(mcp) as client:
        result = await client.call_tool(name, args, raise_on_error=False)
    assert result.is_error
