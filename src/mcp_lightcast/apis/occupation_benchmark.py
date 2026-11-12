"""Occupation benchmarks using the documented dimensions endpoint."""

from typing import Any

from pydantic import TypeAdapter

from .base import BaseLightcastClient, segment


class OccupationBenchmarkAPIClient(BaseLightcastClient):
    def __init__(self) -> None:
        super().__init__("occupation_benchmark")

    async def get_api_metadata(self) -> dict[str, Any]:
        return TypeAdapter(dict[str, Any]).validate_python(
            (await self.get("meta"))["data"]
        )

    async def get_dimension_info(self, dimension: str) -> dict[str, Any]:
        return TypeAdapter(dict[str, Any]).validate_python(
            (await self.get(f"dimensions/{segment(dimension)}"))["data"]
        )

    async def get_benchmark_data(
        self,
        occupation_id: str,
        metrics: list[str] | None = None,
        region: dict[str, str] | None = None,
        dimension: str = "lotocc",
        lot_version: str = "7",
    ) -> dict[str, Any]:
        if dimension not in {"lotocc", "lotspecocc"}:
            raise ValueError("Occupation Benchmark supports lotocc or lotspecocc IDs.")
        data: dict[str, Any] = {"id": occupation_id}
        if metrics is not None:
            data["datasets"] = metrics
        if region is not None:
            data["region"] = region
        # Keep top-level warnings for unavailable datasets instead of fabricating zeros.
        return await self.post(
            f"dimensions/{dimension}", data=data, params={"lot_version": lot_version}
        )
