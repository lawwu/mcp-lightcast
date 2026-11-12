"""Compatibility entry point for the supported title-to-skills workflow."""

from typing import Any

from .normalize_title_get_skills import TitleNormalizationWorkflow


async def normalize_title_and_get_skills(
    title: str, n_skills: int = 10
) -> dict[str, Any]:
    """Return real classification/similarity results, including partial-failure metadata."""
    async with TitleNormalizationWorkflow() as workflow:
        return (
            await workflow.normalize_title_and_get_skills(
                title, max_skills_per_occupation=n_skills
            )
        ).model_dump()
