"""Regression checks against documented endpoint paths, shapes, and filters."""

import json

import pytest

from mcp_lightcast.apis.career_pathways import CareerPathwaysAPIClient
from mcp_lightcast.apis.classification import ClassificationAPIClient
from mcp_lightcast.apis.job_postings import JobPostingsAPIClient
from mcp_lightcast.apis.occupation_benchmark import OccupationBenchmarkAPIClient
from mcp_lightcast.apis.similarity import SimilarityAPIClient
from mcp_lightcast.apis.skills import SkillsAPIClient


async def test_skills_filters_retrieve_related_limit(api_mock):
    item = {
        "id": "KS1",
        "name": "Python",
        "type": {"id": "ST1", "name": "Specialized Skill"},
    }
    for _ in range(3):
        api_mock.add_response(json={"data": [item]})
    async with SkillsAPIClient() as c:
        await c.search_skills("Python", skill_type="ST1")
        await c.get_skills_by_ids(["KS1"])
        await c.get_related_skills("KS1", limit=3)
    a, b, c = api_mock.get_requests()
    assert a.url.params["typeIds"] == "ST1"
    assert "type" not in a.url.params
    assert b.url.path == "/skills/versions/latest/skills"
    assert json.loads(c.content) == {"ids": ["KS1"], "limit": 3}


async def test_unsupported_skill_filters_fail_explicitly():
    async with SkillsAPIClient() as c:
        with pytest.raises(ValueError, match="category filters"):
            await c.search_skills("Python", category="IT")


async def test_classifier_selects_numeric_latest_active_release(api_mock):
    api_mock.add_response(
        json={
            "data": [
                {"release": "2026.9", "removalDate": "2099-01-01T00:00:00Z"},
                {"release": "2026.11", "removalDate": "2099-01-01T00:00:00Z"},
                {"release": "2027.1", "removalDate": "2000-01-01T00:00:00Z"},
            ]
        }
    )
    api_mock.add_response(json={"data": ["skills", "titles"]})
    async with ClassificationAPIClient() as c:
        assert await c.resolve_release() == "2026.11"
        assert await c.get_version_metadata() == {"data": ["skills", "titles"]}
    assert api_mock.get_requests()[1].url.path == "/classifications/2026.11"


async def test_explicit_classifier_release_and_no_fake_normalization(api_mock):
    api_mock.add_response(json={"data": []})
    async with ClassificationAPIClient() as c:
        assert await c.normalize_title("Nothing", version="2026.11") == {"data": []}
    r = api_mock.get_request()
    assert r.url.path == "/classifications/2026.11/titles/normalize"
    assert json.loads(r.content)["terms"] == ["Nothing"]


async def test_similarity_threshold_and_warning_preservation(api_mock):
    api_mock.add_response(json={"data": [], "warning": "Insufficient data"})
    async with SimilarityAPIClient() as c:
        result = await c.query_model(
            "soc", "15-1252", min_score=0.8, filter_ids=["15-1253"]
        )
    assert result["warning"] == "Insufficient data"
    assert json.loads(api_mock.get_request().content)["filter"] == {
        "minScore": 0.8,
        "ids": ["15-1253"],
    }


async def test_similarity_disallows_occupation_lists():
    async with SimilarityAPIClient() as c:
        with pytest.raises(ValueError, match="skill-input"):
            await c.query_model("soc", ["15-1252"])


async def test_benchmark_preserves_unavailable_dataset_warnings(api_mock):
    api_mock.add_response(
        json={"data": {"id": "231715"}, "warnings": ["salary unavailable"]}
    )
    async with OccupationBenchmarkAPIClient() as c:
        r = await c.get_benchmark_data("231715", ["salary"], {"nation": "us"})
    assert r["warnings"]
    req = api_mock.get_request()
    assert req.url.path == "/occupation-benchmark/dimensions/lotocc"
    assert json.loads(req.content) == {
        "id": "231715",
        "datasets": ["salary"],
        "region": {"nation": "us"},
    }


async def test_posting_queries_use_native_filters(api_mock):
    for data in [{"postings": []}, {"unique_postings": 2}, {"ranking": {}}]:
        api_mock.add_response(json={"data": data})
    filters = {"when": "active", "city_name": ["Seattle, WA"]}
    async with JobPostingsAPIClient() as c:
        await c.search_postings(filters, page=2)
        await c.get_postings_summary(filters, ["unique_postings"])
        await c.get_rankings("skills_name", filters, 3)
    a, b, c = api_mock.get_requests()
    assert a.url.path == "/jpa/postings" and json.loads(a.content)["page"] == 2
    assert b.url.path == "/jpa/totals" and json.loads(b.content)["filter"] == filters
    assert (
        c.url.path == "/jpa/rankings/skills_name"
        and json.loads(c.content)["rank"]["limit"] == 3
    )


async def test_pathways_contract(api_mock):
    api_mock.add_response(json={"data": {"pathways": []}})
    api_mock.add_response(json={"data": {"skillGap": []}})
    async with CareerPathwaysAPIClient() as c:
        await c.get_next_steps("23171541", limit=2)
        await c.get_skill_gap("a", "b")
    a, b = api_mock.get_requests()
    assert a.url.path == "/career-pathways/dimensions/lotspecocc/nextstepjobs"
    assert b.url.path == "/career-pathways/dimensions/lotspecocc/skillgap"
    assert json.loads(b.content)["sourceId"] == "a"


async def test_postings_require_timeframe_before_network():
    from pydantic import ValidationError

    async with JobPostingsAPIClient() as c:
        with pytest.raises(ValidationError):
            await c.get_postings_summary({"city_name": ["Seattle, WA"]})
