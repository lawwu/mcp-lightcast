"""Exercise the MCP protocol in-process, not just underlying client methods."""

import json

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_lightcast.server import mcp


def plain(result):
    value = result.structured_content
    return value["result"] if set(value) == {"result"} else value


async def test_catalog_and_resources():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        info = await client.read_resource("lightcast://server/info")
    assert len(tools) == 37
    assert len(resources) == 2
    assert all(t.annotations.read_only_hint for t in tools)
    assert json.loads(info[0].text)["version"] == "0.3.1"


@pytest.mark.parametrize(
    "tool,args",
    [
        ("get_job_title_details", {"title_id": "ET1"}),
        ("bulk_retrieve_titles", {"title_ids": ["ET1"]}),
    ],
)
async def test_title_tools_without_plural_name(api_mock, tool, args):
    data = {"id": "ET1", "name": "Developer"}
    api_mock.add_response(json={"data": [data] if tool.startswith("bulk") else data})
    async with Client(mcp) as client:
        value = plain(await client.call_tool(tool, args))
    assert (value[0] if isinstance(value, list) else value)["id"] == "ET1"


async def test_find_similar_skills_uses_real_method(api_mock):
    api_mock.add_response(json={"data": [{"id": "KS2", "name": "SQL", "score": 0.8}]})
    async with Client(mcp) as client:
        value = plain(
            await client.call_tool("find_similar_skills", {"skill_id": "KS1"})
        )
    assert value["data"][0]["score"] == 0.8


@pytest.mark.parametrize(
    "name,args",
    [
        ("search_skills", {"query": "x", "limit": 0}),
        ("get_related_skills", {"skill_id": "KS1", "limit": 101}),
        ("extract_skills_from_text", {"text": "x", "confidence_threshold": 1.1}),
        ("bulk_retrieve_titles", {"title_ids": []}),
        (
            "normalize_title_and_get_skills",
            {"raw_title": "Developer", "max_occupations": 6},
        ),
        ("search_job_postings", {"filters": {}, "page": 0}),
    ],
)
async def test_mcp_rejects_invalid_inputs_before_network(name, args):
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(name, args)


async def test_posting_analysis_keeps_title_only_ids(api_mock):
    api_mock.add_response(
        json={"data": {"title": {"id": "ET1", "name": "Developer"}, "confidence": 1}}
    )
    api_mock.add_response(
        json={"data": [{"skill": {"id": "KS1", "name": "Python"}, "confidence": 0.8}]}
    )
    api_mock.add_response(
        json={"data": [{"skill": {"id": "KS2", "name": "SQL"}, "confidence": 0.9}]}
    )
    async with Client(mcp) as client:
        result = plain(
            await client.call_tool(
                "analyze_job_posting_skills",
                {"job_title": "Python Developer", "job_description": "SQL"},
            )
        )
    assert {s["id"] for s in result["combined_skills"]} == {"KS1", "KS2"}
    assert result["combined_skills"][0]["sources"] == ["title"]


async def test_mcp_api_errors_are_not_successful_results(api_mock):
    api_mock.add_response(status_code=403, json={"error": "private response"})
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_skill_details", {"skill_id": "KS1"})
