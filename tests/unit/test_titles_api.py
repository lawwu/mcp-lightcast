"""Titles contracts from the current Lightcast reference."""

import json

import pytest

from mcp_lightcast.apis.titles import TitlesAPIClient


@pytest.mark.parametrize("version", ["latest", "5.64"])
async def test_normalize_keeps_requested_version(api_mock, version):
    api_mock.add_response(
        url=f"https://api.lightcast.io/titles/versions/{version}/normalize",
        json={
            "data": {
                "title": {"id": "ET1", "name": "Software Engineer"},
                "confidence": 1,
            }
        },
    )
    async with TitlesAPIClient() as client:
        result = await client.normalize_title("Software Engineer", version)
    assert result["data"]["title"]["id"] == "ET1"
    assert json.loads(api_mock.get_request().content) == {"term": "Software Engineer"}


async def test_search_and_bulk(api_mock):
    api_mock.add_response(json={"data": [{"id": "ET1", "name": "Developer"}]})
    api_mock.add_response(
        json={"data": [{"id": "ET1", "name": "Developer", "pluralName": "Developers"}]}
    )
    async with TitlesAPIClient() as client:
        assert (await client.search_titles("dev", 3))[0].id == "ET1"
        result = await client.bulk_retrieve_titles(["ET1"])
    requests = api_mock.get_requests()
    assert dict(requests[0].url.params) == {"q": "dev", "limit": "3"}
    assert requests[1].url.path == "/titles/versions/latest/titles"
    assert result[0].model_dump()["pluralName"] == "Developers"


async def test_details_dont_require_undocumented_fields(api_mock):
    api_mock.add_response(json={"data": {"id": "ET1", "name": "Developer"}})
    async with TitlesAPIClient() as client:
        assert (await client.get_title_by_id("ET1")).name == "Developer"
