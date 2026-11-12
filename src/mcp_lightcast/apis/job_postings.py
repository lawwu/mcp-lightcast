"""US Job Postings API: query bodies follow the published JPA contract."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseLightcastClient, segment


class PostingTimeframe(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}(-[0-9]{2})?$")
    end: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}(-[0-9]{2})?$")
    type: Literal["posted", "active", "expired"] = "active"


class PostingFilters(BaseModel):
    """A required timeframe plus native JPA filter fields discovered in metadata."""

    model_config = ConfigDict(extra="allow")
    when: Literal["active"] | PostingTimeframe


class JobPostingsAPIClient(BaseLightcastClient):
    def __init__(self) -> None:
        super().__init__("job_postings")

    async def get_postings_metadata(self) -> dict[str, Any]:
        return await self.get("meta")

    async def search_postings(
        self,
        filters: dict[str, Any],
        limit: int = 10,
        page: int = 1,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        return await self.post(
            "postings",
            data={
                "filter": PostingFilters.model_validate(filters).model_dump(
                    exclude_unset=True
                ),
                "limit": limit,
                "page": page,
                "fields": fields
                or ["id", "title_raw", "company_name", "city_name", "posted", "url"],
            },
        )

    async def get_posting_details(self, posting_id: str) -> dict[str, Any]:
        return await self.get(f"postings/{segment(posting_id)}")

    async def get_postings_summary(
        self, filters: dict[str, Any], metrics: list[str] | None = None
    ) -> dict[str, Any]:
        return await self.post(
            "totals",
            data={
                "filter": PostingFilters.model_validate(filters).model_dump(
                    exclude_unset=True
                ),
                "metrics": metrics or ["unique_postings"],
            },
        )

    async def get_rankings(
        self, facet: str, filters: dict[str, Any], limit: int = 10
    ) -> dict[str, Any]:
        return await self.post(
            f"rankings/{segment(facet)}",
            data={
                "filter": PostingFilters.model_validate(filters).model_dump(
                    exclude_unset=True
                ),
                "rank": {"by": "unique_postings", "limit": limit},
            },
        )
