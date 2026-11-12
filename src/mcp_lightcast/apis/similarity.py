"""Similarity models for skills and occupations; preserve upstream warnings."""

from typing import Any

from pydantic import BaseModel, TypeAdapter

from .base import BaseLightcastClient, segment


class SimilarityResult(BaseModel):
    id: str
    name: str
    similarity_score: float
    type: str | None = None


class OccupationSkillMapping(BaseModel):
    occupation_id: str
    occupation_name: str
    skills: list[dict[str, Any]]
    total_skills: int


class SimilarityAPIClient(BaseLightcastClient):
    def __init__(self) -> None:
        super().__init__("similarity")

    async def get_available_models(self) -> list[str]:
        return TypeAdapter(list[str]).validate_python(
            (await self.get("models"))["data"]
        )

    async def get_api_metadata(self) -> dict[str, Any]:
        return TypeAdapter(dict[str, Any]).validate_python(
            (await self.get("meta"))["data"]
        )

    async def get_api_status(self) -> dict[str, Any]:
        return await self.get("status")

    async def query_model(
        self,
        model: str,
        input: str | list[str],
        limit: int = 10,
        min_score: float = 0.5,
        filter_ids: list[str] | None = None,
        lot_version: str = "7",
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100 or not 0 <= min_score <= 1:
            raise ValueError("limit must be 1–100 and min_score must be 0–1.")
        if not input or (
            isinstance(input, list) and (len(input) > 1000 or any(not x for x in input))
        ):
            raise ValueError("Provide an ID or 1–1000 skill IDs.")
        if isinstance(input, list) and not (
            model == "skill" or model.startswith("skill-")
        ):
            raise ValueError("Only skill-input models accept a list of IDs.")
        filters: dict[str, Any] = {"minScore": min_score}
        if filter_ids is not None:
            filters["ids"] = filter_ids
        return await self.post(
            f"models/{segment(model)}",
            data={"input": input, "limit": limit, "filter": filters},
            params={"lot_version": lot_version},
        )

    async def find_similar_skills_bulk(
        self, skill_ids: list[str], limit: int = 10
    ) -> list[dict[str, Any]]:
        return TypeAdapter(list[dict[str, Any]]).validate_python(
            (await self.query_model("skill", skill_ids, limit))["data"]
        )

    async def find_similar_occupations_soc(
        self, soc_code: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return TypeAdapter(list[dict[str, Any]]).validate_python(
            (await self.query_model("soc", soc_code, limit))["data"]
        )

    async def find_similar_occupations_lotocc(
        self, lot_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return TypeAdapter(list[dict[str, Any]]).validate_python(
            (await self.query_model("lotocc", lot_id, limit))["data"]
        )

    async def find_similar_occupations_onet(
        self, onet_code: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return TypeAdapter(list[dict[str, Any]]).validate_python(
            (await self.query_model("onet", onet_code, limit))["data"]
        )
