"""Lightcast Skills API client."""

from typing import Any

from pydantic import BaseModel

from .base import BaseLightcastClient


class SkillType(BaseModel):
    """Skill type model."""
    id: str
    name: str
    description: str | None = None


class SkillSearchResult(BaseModel):
    """Skill search result model."""
    id: str
    name: str
    type: SkillType | None = None
    subcategory: Any | None = None  # Can be string or dict
    category: Any | None = None  # Can be string or dict


class SkillDetail(BaseModel):
    """Detailed skill information."""
    id: str
    name: str
    type: SkillType | None = None
    subcategory: Any | None = None  # Can be string or dict
    category: Any | None = None  # Can be string or dict
    tags: list[Any] | None = None  # Tags can be strings or dict objects
    infoUrl: str | None = None
    description: str | None = None


class ExtractedSkill(BaseModel):
    """Skill extracted from text."""
    skill: SkillDetail
    confidence: float


class SkillsVersionMetadata(BaseModel):
    """Skills version metadata."""
    version: str
    fields: list[str]
    skillCount: int
    removedSkillCount: int
    languageSupport: list[str]
    types: list[SkillType]


class SkillsAPIClient(BaseLightcastClient):
    """Client for Lightcast Skills API."""

    async def search_skills(
        self,
        query: str,
        limit: int = 10,
        skill_type: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        version: str = "latest"
    ) -> list[SkillSearchResult]:
        """Search for skills by name and filters."""
        params = {
            "q": query,
            "limit": limit
        }

        if skill_type:
            params["type"] = skill_type
        if category:
            params["category"] = category
        if subcategory:
            params["subcategory"] = subcategory

        response = await self.get(f"skills/versions/{version}/skills", params=params, version=version)
        return [SkillSearchResult(**item) for item in response.get("data", [])]

    async def get_skill_by_id(
        self,
        skill_id: str,
        version: str = "latest"
    ) -> SkillDetail:
        """Get detailed information about a specific skill."""
        response = await self.get(f"skills/versions/{version}/skills/{skill_id}", version=version)
        return SkillDetail(**response.get("data", {}))

    async def get_skills_by_ids(
        self,
        skill_ids: list[str],
        version: str = "latest"
    ) -> list[SkillDetail]:
        """Get detailed information about multiple skills."""
        data = {"ids": skill_ids}
        response = await self.post(f"skills/versions/{version}/retrieve", data=data, version=version)
        return [SkillDetail(**item) for item in response.get("data", [])]

    async def get_related_skills(
        self,
        skill_id: str,
        limit: int = 10,
        version: str = "latest"
    ) -> list[SkillSearchResult]:
        """Get skills related to a specific skill."""
        params = {"limit": limit}
        response = await self.get(f"skills/versions/{version}/skills/{skill_id}/related", params=params, version=version)
        return [SkillSearchResult(**item) for item in response.get("data", [])]

    async def get_skills_metadata(
        self,
        version: str = "latest"
    ) -> dict[str, Any]:
        """Get metadata about the skills taxonomy."""
        response = await self.get(f"skills/versions/{version}", version=version)
        return response.get("data", {})

    async def get_skill_types(
        self,
        version: str = "latest"
    ) -> list[dict[str, str]]:
        """Get all skill types."""
        metadata = await self.get_version_metadata(version)
        return [{"id": t.id, "name": t.name, "description": t.description} for t in metadata.types]

    async def extract_skills_from_text(
        self,
        text: str,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """Extract skills from a text description."""
        data = {
            "text": text,
            "confidenceThreshold": confidence_threshold
        }
        response = await self.post(f"skills/versions/{version}/extract", data=data, version=version)
        return response.get("data", [])

    async def get_version_metadata(
        self,
        version: str = "latest"
    ) -> SkillsVersionMetadata:
        """Get comprehensive metadata about a skills version."""
        response = await self.get(f"skills/versions/{version}", version=version)
        return SkillsVersionMetadata(**response.get("data", {}))

    async def bulk_retrieve_skills(
        self,
        skill_ids: list[str],
        version: str = "latest"
    ) -> list[SkillDetail]:
        """Retrieve multiple skills by their IDs in a single request."""
        data = {"ids": skill_ids}
        response = await self.post(f"skills/versions/{version}/skills", data=data, version=version)
        return [SkillDetail(**item) for item in response.get("data", [])]

    async def extract_skills_from_text_simple(
        self,
        text: str,
        version: str = "latest"
    ) -> list[ExtractedSkill]:
        """Extract skills from text with default confidence threshold."""
        response = await self.post(f"skills/versions/{version}/extract", data=text, version=version)
        return [ExtractedSkill(**item) for item in response.get("data", [])]
