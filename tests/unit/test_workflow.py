"""Workflow tests use real clients and synthetic, contract-shaped HTTP replies."""

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
