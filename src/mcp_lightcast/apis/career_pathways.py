"""Career transitions and skill gaps from the documented Pathways API."""

from typing import Any

from pydantic import TypeAdapter

from .base import BaseLightcastClient, segment


class CareerPathwaysAPIClient(BaseLightcastClient):
    def __init__(self) -> None:
        super().__init__("career_pathways")

    async def get_api_metadata(self) -> dict[str, Any]:
        return TypeAdapter(dict[str, Any]).validate_python(
            (await self.get("meta"))["data"]
        )

    async def get_available_dimensions(self) -> list[str]:
        return TypeAdapter(list[str]).validate_python(
            (await self.get("dimensions"))["data"]
        )

    async def get_dimension_info(self, dimension: str) -> dict[str, Any]:
        return TypeAdapter(dict[str, Any]).validate_python(
            (await self.get(f"dimensions/{segment(dimension)}"))["data"]
        )

    async def get_next_steps(
        self,
        occupation_id: str,
        dimension: str = "lotspecocc",
        limit: int = 10,
        nation: str = "us",
        categories: list[str] | None = None,
        lot_version: str = "7",
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": occupation_id,
            "limit": limit,
            "region": {"nation": nation},
        }
        if categories is not None:
            data["categories"] = categories
        return await self.post(
            f"dimensions/{segment(dimension)}/nextstepjobs",
            data=data,
            params={"lot_version": lot_version},
        )

    async def get_skill_gap(
        self,
        source_id: str,
        destination_id: str,
        dimension: str = "lotspecocc",
        limit: int = 20,
        nation: str = "us",
        lot_version: str = "7",
    ) -> dict[str, Any]:
        return await self.post(
            f"dimensions/{segment(dimension)}/skillgap",
            data={
                "sourceId": source_id,
                "destinationId": destination_id,
                "limit": limit,
                "region": {"nation": nation},
            },
            params={"lot_version": lot_version},
        )
