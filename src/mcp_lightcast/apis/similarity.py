"""Lightcast Similarity API client."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class SimilarityResult(BaseModel):
    """Similarity result model."""
    id: str
    name: str
    similarity_score: float
    type: Optional[str] = None


class OccupationSkillMapping(BaseModel):
    """Occupation to skills mapping result."""
    occupation_id: str
    occupation_name: str
    skills: List[Dict[str, Any]]
    total_skills: int


class SimilarityAPIClient(BaseLightcastClient):
    """Client for Lightcast Similarity API."""
    
    async def find_similar_occupations(
        self,
        occupation_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        version: str = "2023.4"
    ) -> List[SimilarityResult]:
        """Find occupations similar to a given occupation."""
        params = {
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }
        
        response = await self.get(
            f"similarity/versions/{version}/occupations/{occupation_id}/similar",
            params=params,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]
    
    async def find_similar_skills(
        self,
        skill_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        version: str = "2023.4"
    ) -> List[SimilarityResult]:
        """Find skills similar to a given skill."""
        params = {
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }
        
        response = await self.get(
            f"similarity/versions/{version}/skills/{skill_id}/similar",
            params=params,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]
    
    async def get_occupation_skills(
        self,
        occupation_id: str,
        limit: int = 100,
        skill_type: Optional[str] = None,
        version: str = "2023.4"
    ) -> OccupationSkillMapping:
        """Get skills associated with an occupation."""
        params = {"limit": limit}
        if skill_type:
            params["skill_type"] = skill_type
        
        response = await self.get(
            f"similarity/versions/{version}/occupations/{occupation_id}/skills",
            params=params,
            version=version
        )
        
        data = response.get("data", {})
        return OccupationSkillMapping(
            occupation_id=occupation_id,
            occupation_name=data.get("occupation_name", ""),
            skills=data.get("skills", []),
            total_skills=data.get("total_skills", 0)
        )
    
    async def find_occupations_by_skills(
        self,
        skill_ids: List[str],
        limit: int = 10,
        match_threshold: float = 0.5,
        version: str = "2023.4"
    ) -> List[SimilarityResult]:
        """Find occupations that match a set of skills."""
        data = {
            "skill_ids": skill_ids,
            "limit": limit,
            "match_threshold": match_threshold
        }
        
        response = await self.post(
            f"similarity/versions/{version}/occupations/by_skills",
            data=data,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]
    
    async def calculate_skill_gaps(
        self,
        current_skills: List[str],
        target_occupation_id: str,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """Calculate skill gaps between current skills and target occupation."""
        data = {
            "current_skills": current_skills,
            "target_occupation_id": target_occupation_id
        }
        
        response = await self.post(
            f"similarity/versions/{version}/skill_gaps",
            data=data,
            version=version
        )
        return response.get("data", {})
    
    async def compare_occupations(
        self,
        occupation_id_1: str,
        occupation_id_2: str,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """Compare two occupations and their skill overlap."""
        params = {
            "occupation_1": occupation_id_1,
            "occupation_2": occupation_id_2
        }
        
        response = await self.get(
            f"similarity/versions/{version}/occupations/compare",
            params=params,
            version=version
        )
        return response.get("data", {})