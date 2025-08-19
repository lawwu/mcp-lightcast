"""Lightcast Classification API client."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class ConceptMapping(BaseModel):
    """Concept mapping result model."""
    concept: str
    confidence: float
    mapped_id: str
    mapped_name: str
    mapping_type: str


class ClassificationAPIClient(BaseLightcastClient):
    """Client for Lightcast Classification API."""
    
    async def map_concepts(
        self,
        concepts: List[str],
        target_taxonomy: str = "onet_soc",
        limit: int = 10,
        confidence_threshold: float = 0.5,
        version: str = "2023.4"
    ) -> List[ConceptMapping]:
        """Map concepts to a target taxonomy (e.g., O*NET SOC codes)."""
        data = {
            "concepts": concepts,
            "target_taxonomy": target_taxonomy,
            "limit": limit,
            "confidence_threshold": confidence_threshold
        }
        
        response = await self.post(f"classification/versions/{version}/map_concepts", data=data, version=version)
        return [ConceptMapping(**item) for item in response.get("data", [])]
    
    async def classify_job_title(
        self,
        job_title: str,
        target_taxonomy: str = "onet_soc",
        limit: int = 5,
        version: str = "2023.4"
    ) -> List[ConceptMapping]:
        """Classify a job title to occupation codes."""
        return await self.map_concepts(
            concepts=[job_title],
            target_taxonomy=target_taxonomy,
            limit=limit,
            version=version
        )
    
    async def classify_skills_to_occupations(
        self,
        skills: List[str],
        target_taxonomy: str = "onet_soc",
        limit: int = 10,
        version: str = "2023.4"
    ) -> List[ConceptMapping]:
        """Classify skills to relevant occupations."""
        return await self.map_concepts(
            concepts=skills,
            target_taxonomy=target_taxonomy,
            limit=limit,
            version=version
        )
    
    async def get_supported_taxonomies(
        self,
        version: str = "2023.4"
    ) -> List[Dict[str, str]]:
        """Get list of supported taxonomies for mapping."""
        response = await self.get(f"classification/versions/{version}/taxonomies", version=version)
        return response.get("data", [])
    
    async def batch_classify(
        self,
        items: List[Dict[str, Any]],
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """Perform batch classification of multiple items."""
        data = {"items": items}
        response = await self.post(f"classification/versions/{version}/batch", data=data, version=version)
        return response.get("data", [])