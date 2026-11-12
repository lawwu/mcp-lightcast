"""Composed workflows with explicit provenance and partial-result reporting."""

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from ..apis.classification import ClassificationAPIClient
from ..apis.skills import SkillsAPIClient
from ..apis.titles import TitlesAPIClient
from .normalize_title_get_skills import TitleNormalizationWorkflow
from .types import READ_ONLY, Confidence, Limit, Text


def register_workflow_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"workflows"}, annotations=READ_ONLY)
    async def normalize_title_and_get_skills(
        raw_title: Text,
        max_occupations: Annotated[int, Field(ge=1, le=5)] = 5,
        max_skills_per_occupation: Limit = 20,
        skill_type: str | None = None,
        confidence_threshold: Confidence = 0.5,
        version: Text = "latest",
        classification_version: Text = "latest",
        lot_version: Literal["6", "7"] = "7",
    ) -> dict[str, Any]:
        """Normalize a title, classify to LOT specialized occupations, then retrieve associated skills from Similarity. Requires three API permissions. Reports partial failures; version controls Titles only, classification_version controls classifiers, and lot_version must match the classifier's LOT major version."""
        async with TitleNormalizationWorkflow() as workflow:
            return (
                await workflow.normalize_title_and_get_skills(
                    raw_title,
                    max_occupations,
                    max_skills_per_occupation,
                    skill_type,
                    confidence_threshold,
                    version,
                    classification_version,
                    lot_version,
                )
            ).model_dump()

    @mcp.tool(tags={"workflows"}, annotations=READ_ONLY)
    async def analyze_job_posting_skills(
        job_title: Text,
        job_description: str,
        extract_from_description: bool = True,
        confidence_threshold: Confidence = 0.5,
        version: Text = "latest",
        skills_version: Text = "latest",
    ) -> dict[str, Any]:
        """Normalize a title and extract skills explicitly present in its title/description. Does not infer occupation skills. version controls Titles; skills_version controls Skills."""
        async with TitlesAPIClient() as titles, SkillsAPIClient() as skills:
            normalized = await titles.normalize_title(job_title, version)
            title_skills = await skills.extract_skills_from_text(
                job_title, confidence_threshold, skills_version
            )
            description_skills = (
                await skills.extract_skills_from_text(
                    job_description, confidence_threshold, skills_version
                )
                if extract_from_description and job_description
                else []
            )
        combined: dict[str, dict[str, Any]] = {}
        for source, items in (
            ("title", title_skills),
            ("description", description_skills),
        ):
            for item in items:
                skill = item["skill"]
                if skill["id"] not in combined:
                    combined[skill["id"]] = {
                        **skill,
                        "confidence": item["confidence"],
                        "sources": [],
                    }
                combined[skill["id"]]["confidence"] = max(
                    combined[skill["id"]]["confidence"], item["confidence"]
                )
                combined[skill["id"]]["sources"].append(source)
        return {
            "job_title": job_title,
            "normalized_title": normalized.get("data"),
            "title_skills": title_skills,
            "description_skills": description_skills,
            "combined_skills": list(combined.values()),
            "total_unique_skills": len(combined),
        }

    @mcp.tool(tags={"workflows"}, annotations=READ_ONLY)
    async def normalize_title_and_extract_skills(
        title: Text, confidence_threshold: Confidence = 0.6, version: Text = "latest"
    ) -> dict[str, Any]:
        """Normalize a title and extract explicitly mentioned skills using the current Classification release. May consume two classifier quota requests."""
        async with ClassificationAPIClient() as client:
            normalized = await client.normalize_title(
                title, confidence_threshold, version
            )
            extracted = await client.extract_skills_from_text(
                title, confidence_threshold, version=version
            )
            return {
                "title": title,
                "normalization": normalized,
                "extraction_method": "classification_api",
                "skills": [s.model_dump() for s in extracted.concepts],
                "warnings": extracted.warnings,
            }
