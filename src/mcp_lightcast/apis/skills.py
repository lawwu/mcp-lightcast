"""Lightcast Skills API client."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class SkillType(BaseModel):
    """Skill type model."""
    id: str
    name: str


class SkillSearchResult(BaseModel):
    """Skill search result model."""
    id: str
    name: str
    type: Optional[SkillType] = None
    subcategory: Optional[Any] = None  # Can be string or dict
    category: Optional[Any] = None  # Can be string or dict


class SkillDetail(BaseModel):
    """Detailed skill information."""
    id: str
    name: str
    type: Optional[SkillType] = None
    subcategory: Optional[Any] = None  # Can be string or dict
    category: Optional[Any] = None  # Can be string or dict
    tags: Optional[List[Any]] = None  # Tags can be strings or dict objects
    infoUrl: Optional[str] = None
    description: Optional[str] = None


class ExtractedSkill(BaseModel):
    """Skill extracted from text."""
    skill: SkillDetail
    confidence: float


class SkillsVersionMetadata(BaseModel):
    """Skills version metadata."""
    version: str
    fields: List[str]
    skillCount: int
    removedSkillCount: int
    languageSupport: List[str]
    types: List[SkillType]


class SkillsAPIClient(BaseLightcastClient):
    """Client for Lightcast Skills API."""
    
    async def search_skills(
        self,
        query: str,
        limit: int = 10,
        skill_type: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        version: str = "latest"
    ) -> List[SkillSearchResult]:
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
        skill_ids: List[str],
        version: str = "latest"
    ) -> List[SkillDetail]:
        """Get detailed information about multiple skills."""
        data = {"ids": skill_ids}
        response = await self.post(f"skills/versions/{version}/retrieve", data=data, version=version)
        return [SkillDetail(**item) for item in response.get("data", [])]
    
    async def get_related_skills(
        self,
        skill_id: str,
        limit: int = 10,
        version: str = "latest"
    ) -> List[SkillSearchResult]:
        """Get skills related to a specific skill."""
        params = {"limit": limit}
        response = await self.get(f"skills/versions/{version}/skills/{skill_id}/related", params=params, version=version)
        return [SkillSearchResult(**item) for item in response.get("data", [])]
    
    async def get_skills_metadata(
        self,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """Get metadata about the skills taxonomy."""
        response = await self.get(f"skills/versions/{version}/meta", version=version)
        return response.get("data", {})
    
    async def get_skill_categories(
        self,
        version: str = "latest"
    ) -> List[Dict[str, str]]:
        """Get all skill categories and subcategories."""
        response = await self.get(f"skills/versions/{version}/categories", version=version)
        return response.get("data", [])
    
    async def extract_skills_from_text(
        self,
        text: str,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> List[Dict[str, Any]]:
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
        skill_ids: List[str],
        version: str = "latest"
    ) -> List[SkillDetail]:
        """Retrieve multiple skills by their IDs in a single request."""
        data = {"ids": skill_ids}
        response = await self.post(f"skills/versions/{version}/skills", data=data, version=version)
        return [SkillDetail(**item) for item in response.get("data", [])]
    
    async def extract_skills_from_text_simple(
        self,
        text: str,
        version: str = "latest"
    ) -> List[ExtractedSkill]:
        """Extract skills from text with default confidence threshold."""
        response = await self.post(f"skills/versions/{version}/extract", data=text, version=version)
        return [ExtractedSkill(**item) for item in response.get("data", [])]