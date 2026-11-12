"""A real title → LOT occupation → Similarity skills workflow."""

from contextlib import AsyncExitStack
from typing import Any, Self

from pydantic import BaseModel

from ..apis.base import APIError
from ..apis.classification import ClassificationAPIClient
from ..apis.similarity import SimilarityAPIClient
from ..apis.skills import SkillsAPIClient
from ..apis.titles import TitlesAPIClient
from ..auth.oauth import AuthenticationError


class NormalizedTitleWithSkills(BaseModel):
    raw_title: str
    normalized_title: dict[str, Any]
    occupation_mappings: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    workflow_metadata: dict[str, Any]


class TitleNormalizationWorkflow:
    def __init__(self) -> None:
        self.titles_client = TitlesAPIClient()
        self.classification_client = ClassificationAPIClient()
        self.similarity_client = SimilarityAPIClient()
        self.skills_client = SkillsAPIClient()
        self._stack = AsyncExitStack()

    async def __aenter__(self) -> Self:
        for client in (
            self.titles_client,
            self.classification_client,
            self.similarity_client,
            self.skills_client,
        ):
            await self._stack.enter_async_context(client)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        return await self._stack.__aexit__(exc_type, exc_val, exc_tb)

    async def normalize_title_and_get_skills(
        self,
        raw_title: str,
        max_occupations: int = 5,
        max_skills_per_occupation: int = 20,
        skill_type: str | None = None,
        confidence_threshold: float = 0.5,
        version: str = "latest",
        classification_version: str = "latest",
        lot_version: str = "7",
    ) -> NormalizedTitleWithSkills:
        metadata: dict[str, Any] = {
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "status": "complete",
        }
        response = await self.titles_client.normalize_title(raw_title, version)
        metadata["steps_completed"].append("title_normalization")
        data = response.get("data") or {}
        title = data.get("title") or {}
        normalized = {**title, "confidence": data.get("confidence")} if title else {}
        occupations: list[dict[str, Any]] = []
        skills: dict[str, dict[str, Any]] = {}
        if not title:
            metadata["status"] = "no_match"
            return NormalizedTitleWithSkills(
                raw_title=raw_title,
                normalized_title={},
                occupation_mappings=[],
                skills=[],
                workflow_metadata=metadata,
            )
        try:
            response = await self.classification_client.classify_occupation(
                title["name"],
                limit=max_occupations,
                confidence_threshold=confidence_threshold,
                version=classification_version,
            )
            metadata["warnings"].extend(response.get("warnings", []))
            metadata["steps_completed"].append("occupation_classification")
            for item in response["data"]:
                concept = item["concept"]
                occupations.append(
                    {
                        "occupation_id": concept["id"],
                        "occupation_name": concept["name"],
                        "confidence": item["confidence"],
                        "taxonomy": "lotspecocc",
                    }
                )
                try:
                    matches = await self.similarity_client.query_model(
                        "lotspecocc-skill",
                        concept["id"],
                        max_skills_per_occupation,
                        lot_version=lot_version,
                    )
                    metadata["warnings"].extend(matches.get("warnings", []))
                    if matches.get("warning"):
                        metadata["warnings"].append(matches["warning"])
                    for skill in matches["data"]:
                        sid = skill["id"]
                        if sid not in skills:
                            skills[sid] = {**skill, "source_occupations": []}
                        skills[sid]["score"] = max(
                            skills[sid].get("score", 0), skill.get("score", 0)
                        )
                        skills[sid]["source_occupations"].append(concept["id"])
                except (APIError, AuthenticationError) as exc:
                    metadata["errors"].append(f"Skills for {concept['id']}: {exc}")
            if not metadata["errors"]:
                metadata["steps_completed"].append("occupation_skills")
            if skill_type and skills:
                details = await self.skills_client.bulk_retrieve_skills(list(skills))
                allowed = {
                    s.id
                    for s in details
                    if s.type and skill_type in {s.type.id, s.type.name}
                }
                skills = {k: v for k, v in skills.items() if k in allowed}
        except (APIError, AuthenticationError) as exc:
            metadata["errors"].append(str(exc))
        if metadata["errors"]:
            metadata["status"] = "partial"
        elif not occupations:
            metadata["status"] = "no_occupation_match"
        return NormalizedTitleWithSkills(
            raw_title=raw_title,
            normalized_title=normalized,
            occupation_mappings=occupations,
            skills=sorted(
                skills.values(), key=lambda s: s.get("score", 0), reverse=True
            ),
            workflow_metadata=metadata,
        )

    async def get_title_skills_simple(
        self, raw_title: str, limit: int = 50, version: str = "latest"
    ) -> dict[str, Any]:
        result = await self.normalize_title_and_get_skills(
            raw_title, max_skills_per_occupation=min(limit, 100), version=version
        )
        return {
            "normalized_title": result.normalized_title.get("name"),
            "confidence": result.normalized_title.get("confidence"),
            "skills": result.skills[:limit],
            "skills_count": len(result.skills),
            "top_occupations": [
                o["occupation_name"] for o in result.occupation_mappings
            ],
            "workflow_metadata": result.workflow_metadata,
        }
