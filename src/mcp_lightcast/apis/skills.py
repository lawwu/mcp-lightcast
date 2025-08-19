"""Lightcast Skills API client."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class SkillSearchResult(BaseModel):
    """Skill search result model."""
    id: str
    name: str
    type: Optional[str] = None
    subcategory: Optional[str] = None
    category: Optional[str] = None


class SkillDetail(BaseModel):
    """Detailed skill information."""
    id: str
    name: str
    type: Optional[str] = None
    subcategory: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    infoUrl: Optional[str] = None
    description: Optional[str] = None


class SkillsAPIClient(BaseLightcastClient):
    """Client for Lightcast Skills API."""
    
    async def search_skills(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        skill_type: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        version: str = "2023.4"
    ) -> List[SkillSearchResult]:
        """Search for skills by name and filters."""
        params = {
            "q": query,
            "limit": limit,
            "offset": offset
        }
        
        if skill_type:
            params["type"] = skill_type
        if category:
            params["category"] = category
        if subcategory:
            params["subcategory"] = subcategory
        
        response = await self.get(f"skills/versions/{version}", params=params, version=version)
        return [SkillSearchResult(**item) for item in response.get("data", [])]
    
    async def get_skill_by_id(
        self,
        skill_id: str,
        version: str = "2023.4"
    ) -> SkillDetail:
        """Get detailed information about a specific skill."""
        response = await self.get(f"skills/versions/{version}/{skill_id}", version=version)
        return SkillDetail(**response.get("data", {}))
    
    async def get_skills_by_ids(
        self,
        skill_ids: List[str],
        version: str = "2023.4"
    ) -> List[SkillDetail]:
        """Get detailed information about multiple skills."""
        data = {"ids": skill_ids}
        response = await self.post(f"skills/versions/{version}/retrieve", data=data, version=version)
        return [SkillDetail(**item) for item in response.get("data", [])]
    
    async def get_related_skills(
        self,
        skill_id: str,
        limit: int = 10,
        version: str = "2023.4"
    ) -> List[SkillSearchResult]:
        """Get skills related to a specific skill."""
        params = {"limit": limit}
        response = await self.get(f"skills/versions/{version}/{skill_id}/related", params=params, version=version)
        return [SkillSearchResult(**item) for item in response.get("data", [])]
    
    async def get_skills_metadata(
        self,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """Get metadata about the skills taxonomy."""
        response = await self.get(f"skills/versions/{version}/meta", version=version)
        return response.get("data", {})
    
    async def get_skill_categories(
        self,
        version: str = "2023.4"
    ) -> List[Dict[str, str]]:
        """Get all skill categories and subcategories."""
        response = await self.get(f"skills/versions/{version}/categories", version=version)
        return response.get("data", [])
    
    async def extract_skills_from_text(
        self,
        text: str,
        confidence_threshold: float = 0.5,
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """Extract skills from a text description."""
        data = {
            "text": text,
            "confidence_threshold": confidence_threshold
        }
        response = await self.post(f"skills/versions/{version}/extract", data=data, version=version)
        return response.get("data", [])