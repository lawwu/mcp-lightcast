"""Lightcast taxonomy discovery, mapping, and current classifiers."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter

from .base import APIError, BaseLightcastClient, segment


class SkillExtractionResult(BaseModel):
    concept: dict[str, Any]
    confidence: float


class SkillsExtractionResult(BaseModel):
    concepts: list[SkillExtractionResult]
    trace: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[Any] = Field(default_factory=list)


class ClassificationAPIClient(BaseLightcastClient):
    def __init__(self) -> None:
        super().__init__("classification")
        self._release: str | None = None

    async def get_releases(self) -> list[dict[str, Any]]:
        return TypeAdapter(list[dict[str, Any]]).validate_python(
            (await self.get("classifications"))["data"]
        )

    async def get_available_versions(self) -> list[str]:
        return [r["release"] for r in await self.get_releases()]

    async def resolve_release(self, version: str = "latest") -> str:
        if version != "latest":
            return segment(version)
        if self._release is None:
            now = datetime.now(UTC)
            releases = [
                r
                for r in await self.get_releases()
                if not r.get("removalDate")
                or datetime.fromisoformat(r["removalDate"].replace("Z", "+00:00")) > now
            ]
            if not releases:
                raise APIError(
                    "No active Classification releases are available for this account."
                )
            self._release = max(
                releases, key=lambda r: tuple(int(n) for n in r["release"].split("."))
            )["release"]
        return self._release

    async def get_version_metadata(self, version: str = "latest") -> dict[str, Any]:
        release = await self.resolve_release(version)
        # This endpoint returns source types (a list), not a taxonomy metadata dict.
        return await self.get(f"classifications/{release}")

    async def extract_skills_from_text(
        self,
        text: str,
        confidence_threshold: float = 0.6,
        trace: bool = True,
        input_locale: str = "en-US",
        output_locale: str = "en-US",
        version: str = "latest",
    ) -> SkillsExtractionResult:
        release = await self.resolve_release(version)
        response = await self.post(
            f"classifications/{release}/skills/extract",
            data={
                "text": text,
                "confidenceThreshold": confidence_threshold,
                "trace": trace,
                "inputLocale": input_locale,
                "outputLocale": output_locale,
            },
        )
        return SkillsExtractionResult(
            **response["data"], warnings=response.get("warnings", [])
        )

    async def normalize_title(
        self,
        title_text: str,
        confidence_threshold: float = 0.6,
        version: str = "latest",
    ) -> dict[str, Any]:
        release = await self.resolve_release(version)
        return await self.post(
            f"classifications/{release}/titles/normalize",
            data={
                "terms": [title_text],
                "limit": 1,
                "confidenceThreshold": confidence_threshold,
                "fields": ["id", "name"],
            },
        )

    async def classify_occupation(
        self,
        title: str,
        description: str = "",
        limit: int = 5,
        confidence_threshold: float = 0.5,
        version: str = "latest",
    ) -> dict[str, Any]:
        release = await self.resolve_release(version)
        return await self.post(
            f"classifications/{release}/lot/classify",
            data={
                "title": title,
                "description": description,
                "limit": limit,
                "confidenceThreshold": confidence_threshold,
                "fields": ["id", "name", "level", "parentId"],
            },
        )

    async def get_available_mappings(self) -> list[dict[str, Any]]:
        return TypeAdapter(list[dict[str, Any]]).validate_python(
            (await self.get("mappings"))["data"]
        )

    async def map_concepts(
        self, mapping_name: str, id_list: list[str]
    ) -> dict[str, Any]:
        return await self.post(
            f"mappings/{segment(mapping_name)}", data={"ids": id_list}
        )

    async def get_taxonomies(self) -> dict[str, Any]:
        return await self.get("taxonomies")

    async def get_api_status(self) -> dict[str, Any]:
        return await self.get("status")
