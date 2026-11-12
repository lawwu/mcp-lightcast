"""Lightcast Titles API client."""

from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter

from .base import BaseLightcastClient, segment


class TitleSearchResult(BaseModel):
    """Title search result model."""

    id: str
    name: str
    type: str | None = None


class TitleDetail(BaseModel):
    """Detailed title information, including optional licensed mappings."""

    model_config = ConfigDict(extra="allow")
    mappings: list[dict[str, Any]] | None = None
    id: str
    name: str
    type: str | None = None
    parent: dict[str, Any] | None = None
    children: list[dict[str, Any]] | None = None


class TitleNormalizationResult(BaseModel):
    """Title normalization result."""

    confidence: float
    title: TitleDetail
    jobLevels: list[str] | None = None


class TitlesVersionMetadata(BaseModel):
    """Titles version metadata."""

    version: str
    fields: list[str]
    titleCount: int
    removedTitleCount: int


class TitlesGeneralMetadata(BaseModel):
    """General titles metadata."""

    attribution: dict[str, Any]
    latestVersion: str


class TitlesAPIClient(BaseLightcastClient):
    """Client for Lightcast Titles API."""

    def __init__(self) -> None:
        super().__init__(api_name="titles")

    async def search_titles(
        self, query: str, limit: int = 10, version: str = "latest"
    ) -> list[TitleSearchResult]:
        """Search for titles by name."""
        params = {"q": query, "limit": limit}

        response = await self.get(
            f"versions/{segment(version)}/titles", params=params, version=version
        )
        return [TitleSearchResult(**item) for item in response.get("data", [])]

    async def get_title_by_id(
        self, title_id: str, version: str = "latest"
    ) -> TitleDetail:
        """Get detailed information about a specific title."""
        response = await self.get(
            f"versions/{segment(version)}/titles/{segment(title_id)}", version=version
        )
        return TitleDetail(**response.get("data", {}))

    async def normalize_title(
        self, raw_title: str, version: str = "latest"
    ) -> dict[str, Any]:
        """Normalize a raw job title string to the best matching Lightcast title."""
        response = await self.post(
            f"versions/{segment(version)}/normalize",
            data={"term": raw_title},
            version=version,
        )
        return response

    async def get_titles_metadata(self, version: str = "latest") -> dict[str, Any]:
        """Get metadata about the titles taxonomy."""
        response = await self.get(f"versions/{segment(version)}", version=version)
        return TypeAdapter(dict[str, Any]).validate_python(response.get("data", {}))

    async def get_version_metadata(
        self, version: str = "latest"
    ) -> TitlesVersionMetadata:
        """Get comprehensive metadata about a titles version."""
        response = await self.get(f"versions/{segment(version)}", version=version)
        return TitlesVersionMetadata(**response.get("data", {}))

    async def get_general_metadata(self) -> TitlesGeneralMetadata:
        """Get general titles taxonomy metadata."""
        response = await self.get("meta")
        return TitlesGeneralMetadata(**response.get("data", {}))

    async def bulk_retrieve_titles(
        self, title_ids: list[str], version: str = "latest"
    ) -> list[TitleDetail]:
        """Retrieve multiple titles by their IDs in a single request."""
        data = {"ids": title_ids}
        response = await self.post(
            f"versions/{segment(version)}/titles", data=data, version=version
        )
        return [TitleDetail(**item) for item in response.get("data", [])]
