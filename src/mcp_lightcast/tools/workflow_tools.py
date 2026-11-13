"""Composed workflows with explicit provenance and partial-result reporting."""

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from .. import workflows
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
        return await workflows.normalize_title_and_get_skills(
            raw_title,
            max_occupations,
            max_skills_per_occupation,
            skill_type,
            confidence_threshold,
            version,
            classification_version,
            lot_version,
        )

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
        return await workflows.analyze_job_posting_skills(
            job_title,
            job_description,
            extract_from_description,
            confidence_threshold,
            version,
            skills_version,
        )

    @mcp.tool(tags={"workflows"}, annotations=READ_ONLY)
    async def normalize_title_and_extract_skills(
        title: Text, confidence_threshold: Confidence = 0.6, version: Text = "latest"
    ) -> dict[str, Any]:
        """Normalize a title and extract explicitly mentioned skills using the current Classification release. May consume two classifier quota requests."""
        return await workflows.normalize_title_and_extract_skills(
            title, confidence_threshold, version
        )
