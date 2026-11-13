"""Workflow tests use real clients and synthetic, contract-shaped HTTP replies."""

import json

import httpx
import pytest

from mcp_lightcast import workflows
from mcp_lightcast.apis.base import APIError
from mcp_lightcast.tools.normalize_title_get_skills import TitleNormalizationWorkflow


def add_title(api_mock, data=None):
    api_mock.add_response(
        url="https://api.lightcast.io/titles/versions/latest/normalize",
        json={
            "data": data
            if data is not None
            else {"title": {"id": "ET1", "name": "Developer"}, "confidence": 1}
        },
    )


def add_occupations(api_mock, occupations):
    api_mock.add_response(
        url="https://classification.emsicloud.com/classifications/2026.11/lot/classify",
        json={
            "data": [
                {"confidence": 0.9, "concept": {"id": oid, "name": f"Role {oid}"}}
                for oid in occupations
            ]
        },
    )


async def test_complete_workflow_deduplicates_and_keeps_provenance(api_mock):
    add_title(api_mock)
    add_occupations(api_mock, ["A", "B"])
    api_mock.add_response(
        json={"data": [{"id": "KS1", "name": "Python", "score": 0.8}]}
    )
    api_mock.add_response(
        json={"data": [{"id": "KS1", "name": "Python", "score": 0.9}]}
    )
    async with TitleNormalizationWorkflow() as w:
        result = await w.normalize_title_and_get_skills(
            "Developer", classification_version="2026.11"
        )
    assert result.workflow_metadata["status"] == "complete"
    assert result.workflow_metadata["steps_completed"] == [
        "title_normalization",
        "occupation_classification",
        "occupation_skills",
    ]
    assert len(result.skills) == 1
    assert result.skills[0]["score"] == 0.9
    assert result.skills[0]["source_occupations"] == ["A", "B"]
    assert api_mock.get_requests()[2].url.path == "/similarity/models/lotspecocc-skill"


async def test_partial_result_does_not_claim_success(api_mock):
    add_title(api_mock)
    add_occupations(api_mock, ["A"])
    api_mock.add_response(status_code=403, json={"error": "restricted"})
    async with TitleNormalizationWorkflow() as w:
        result = await w.normalize_title_and_get_skills(
            "Developer", classification_version="2026.11"
        )
    assert result.normalized_title["id"] == "ET1"
    assert result.workflow_metadata["status"] == "partial"
    assert result.workflow_metadata["errors"]
    assert "occupation_skills" not in result.workflow_metadata["steps_completed"]


async def test_no_title_match_stops_without_extra_requests(api_mock):
    add_title(api_mock, {})
    async with TitleNormalizationWorkflow() as w:
        result = await w.normalize_title_and_get_skills("Unknown")
    assert result.workflow_metadata["status"] == "no_match"
    assert not result.skills
    assert len(api_mock.get_requests()) == 1


async def test_upstream_warning_is_preserved(api_mock):
    add_title(api_mock)
    add_occupations(api_mock, ["A"])
    api_mock.add_response(json={"data": [], "warning": "Insufficient evidence"})
    async with TitleNormalizationWorkflow() as w:
        result = await w.normalize_title_and_get_skills(
            "Developer", classification_version="2026.11"
        )
    assert result.workflow_metadata["warnings"] == ["Insufficient evidence"]


async def test_posting_extraction_keeps_first_details_strongest_confidence_and_sources(
    api_mock,
):
    add_title(api_mock)
    api_mock.add_response(
        json={
            "data": [
                {"skill": {"id": "KS1", "name": "Python"}, "confidence": 0.8},
                {"skill": {"id": "KS2", "name": "SQL"}, "confidence": 0.7},
            ]
        }
    )
    api_mock.add_response(
        json={
            "data": [
                {
                    "skill": {"id": "KS1", "name": "Different later label"},
                    "confidence": 0.9,
                },
                {"skill": {"id": "KS1", "name": "Another mention"}, "confidence": 0.6},
            ]
        }
    )
    result = await workflows.analyze_job_posting_skills("Developer", "Python")
    assert result["combined_skills"] == [
        {
            "id": "KS1",
            "name": "Python",
            "confidence": 0.9,
            "sources": ["title", "description", "description"],
        },
        {"id": "KS2", "name": "SQL", "confidence": 0.7, "sources": ["title"]},
    ]
    assert result["total_unique_skills"] == 2
    assert result["title_skills"][0]["confidence"] == 0.8
    assert result["normalized_title"]["title"]["id"] == "ET1"


@pytest.mark.parametrize("description,enabled", [("", True), ("Python", False)])
async def test_posting_extraction_skips_unrequested_description(
    api_mock, description, enabled
):
    add_title(api_mock)
    api_mock.add_response(json={"data": []})
    result = await workflows.analyze_job_posting_skills(
        "Developer", description, enabled
    )
    assert result["description_skills"] == []
    assert result["total_unique_skills"] == 0
    assert len(api_mock.get_requests()) == 2


@pytest.mark.parametrize("failed_stage", [0, 1, 2])
async def test_posting_extraction_required_stage_failure_propagates(
    api_mock, failed_stage
):
    if failed_stage > 0:
        add_title(api_mock)
    if failed_stage > 1:
        api_mock.add_response(json={"data": []})
    api_mock.add_response(status_code=403)
    with pytest.raises(APIError, match="403"):
        await workflows.analyze_job_posting_skills("Developer", "Python")
    assert len(api_mock.get_requests()) == failed_stage + 1


async def test_classifier_composition_shares_release_and_preserves_both_warning_locations(
    api_mock,
):
    api_mock.add_response(json={"data": [{"release": "2026.11"}]})
    normalization = {"data": [], "warnings": ["normalization warning"]}
    api_mock.add_response(json=normalization)
    api_mock.add_response(
        json={
            "data": {
                "concepts": [
                    {"concept": {"id": "KS1", "name": "Python"}, "confidence": 0.9}
                ]
            },
            "warnings": ["extraction warning"],
        }
    )
    result = await workflows.normalize_title_and_extract_skills("Python Developer")
    assert result == {
        "title": "Python Developer",
        "normalization": normalization,
        "extraction_method": "classification_api",
        "skills": [{"concept": {"id": "KS1", "name": "Python"}, "confidence": 0.9}],
        "warnings": ["extraction warning"],
    }
    requests = api_mock.get_requests()
    assert [request.url.path for request in requests] == [
        "/classifications",
        "/classifications/2026.11/titles/normalize",
        "/classifications/2026.11/skills/extract",
    ]
    assert json.loads(requests[-1].content)["confidenceThreshold"] == 0.6


@pytest.mark.parametrize("failed_stage", [0, 1])
async def test_classifier_composition_required_failures_propagate(
    api_mock, failed_stage
):
    if failed_stage:
        api_mock.add_response(json={"data": []})
    api_mock.add_response(status_code=403)
    with pytest.raises(APIError, match="403"):
        await workflows.normalize_title_and_extract_skills(
            "Developer", version="2026.11"
        )
    assert len(api_mock.get_requests()) == failed_stage + 1


async def test_inference_retains_success_when_an_occupation_fails(api_mock):
    add_title(api_mock)
    add_occupations(api_mock, ["A", "B"])
    api_mock.add_response(
        json={"data": [{"id": "KS1", "name": "Python", "score": 0.9}]}
    )
    api_mock.add_response(status_code=403)
    result = await workflows.normalize_title_and_get_skills(
        "Developer", classification_version="2026.11"
    )
    assert result["skills"] == [
        {"id": "KS1", "name": "Python", "score": 0.9, "source_occupations": ["A"]}
    ]
    assert result["workflow_metadata"]["status"] == "partial"
    assert result["workflow_metadata"]["errors"][0].startswith("Skills for B:")
    assert "occupation_skills" not in result["workflow_metadata"]["steps_completed"]


@pytest.mark.parametrize("failure", [False, True])
async def test_optional_type_filter_preserves_existing_failure_policy(
    api_mock, failure
):
    add_title(api_mock)
    add_occupations(api_mock, ["A"])
    api_mock.add_response(
        json={
            "data": [
                {"id": "KS1", "name": "Python", "score": 0.9},
                {"id": "KS2", "name": "Communication", "score": 0.8},
            ]
        }
    )
    api_mock.add_response(
        status_code=403 if failure else 200,
        json={
            "data": [
                {
                    "id": "KS1",
                    "name": "Python",
                    "type": {"id": "ST1", "name": "Specialized"},
                },
                {
                    "id": "KS2",
                    "name": "Communication",
                    "type": {"id": "ST2", "name": "Common"},
                },
            ]
        },
    )
    result = await workflows.normalize_title_and_get_skills(
        "Developer", skill_type="ST1", classification_version="2026.11"
    )
    assert [skill["id"] for skill in result["skills"]] == (
        ["KS1", "KS2"] if failure else ["KS1"]
    )
    assert result["workflow_metadata"]["status"] == (
        "partial" if failure else "complete"
    )


async def test_inference_reports_no_occupation_match(api_mock):
    add_title(api_mock)
    add_occupations(api_mock, [])
    result = await workflows.normalize_title_and_get_skills(
        "Developer", classification_version="2026.11"
    )
    assert result["workflow_metadata"]["status"] == "no_occupation_match"
    assert not result["skills"]


async def test_inference_does_not_disguise_programming_errors(api_mock):
    add_title(api_mock)
    api_mock.add_exception(RuntimeError("broken implementation"))
    with pytest.raises(RuntimeError, match="broken implementation"):
        await workflows.normalize_title_and_get_skills(
            "Developer", classification_version="2026.11"
        )


async def test_inference_initial_failure_propagates(api_mock):
    api_mock.add_response(status_code=403)
    with pytest.raises(APIError, match="403"):
        await workflows.normalize_title_and_get_skills("Developer")


@pytest.mark.parametrize(
    "name,arguments",
    [
        (
            "normalize_title_and_get_skills",
            {"raw_title": "Developer", "classification_version": "2026.11"},
        ),
        (
            "analyze_job_posting_skills",
            {"job_title": "Developer", "job_description": "Python"},
        ),
        (
            "normalize_title_and_extract_skills",
            {"title": "Developer", "version": "2026.11"},
        ),
    ],
)
async def test_mcp_adapter_preserves_direct_workflow_results(api_mock, name, arguments):
    from fastmcp import Client

    from mcp_lightcast.server import create_server

    def respond(request):
        path = request.url.path
        if path.endswith("/normalize"):
            data = {"title": {"id": "ET1", "name": "Developer"}, "confidence": 1}
        elif path.endswith("/lot/classify"):
            data = [{"concept": {"id": "A", "name": "Developer"}, "confidence": 0.8}]
        elif "/similarity/" in path:
            data = [{"id": "KS1", "name": "Python", "score": 0.9}]
        elif "/classifications/" in path:
            data = {"concepts": [{"concept": {"id": "KS1"}, "confidence": 0.9}]}
        else:
            data = [{"skill": {"id": "KS1", "name": "Python"}, "confidence": 0.9}]
        return httpx.Response(200, json={"data": data})

    api_mock.add_callback(respond, is_reusable=True)
    expected = await getattr(workflows, name)(**arguments)
    async with Client(create_server()) as client:
        actual = await client.call_tool(name, arguments)
    assert actual.structured_content == expected
