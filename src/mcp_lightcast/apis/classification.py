"""Lightcast Classification API client."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class OccupationMapping(BaseModel):
    """Occupation mapping result."""
    id: str
    title: str
    code: str = Field(alias="soc_code", default="")
    confidence: float
    type: Optional[str] = None


class ConceptMapping(BaseModel):
    """Concept mapping result."""
    concept: str
    occupations: List[OccupationMapping]


class TitleNormalizationResult(BaseModel):
    """Title normalization result."""
    normalized_title: str
    soc_code: str
    confidence: float
    alternatives: Optional[List[Dict[str, Any]]] = None


class SkillsExtractionResult(BaseModel):
    """Skills extraction result."""
    extracted_skills: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]


class BulkClassificationRequest(BaseModel):
    """Bulk classification request."""
    concepts: List[str]
    options: Optional[Dict[str, Any]] = None


class ClassificationAPIClient(BaseLightcastClient):
    """Client for Lightcast Classification API."""
    
    def __init__(self):
        super().__init__(api_name="classification")
    
    async def map_concepts_to_occupations(
        self,
        concepts: List[str],
        limit: int = 10,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> List[ConceptMapping]:
        """
        Map concepts to relevant occupations.
        
        Args:
            concepts: List of concepts/job titles to map
            limit: Maximum number of occupations per concept
            confidence_threshold: Minimum confidence score
            version: API version to use
            
        Returns:
            List of concept mappings with occupations
        """
        data = {
            "concepts": concepts,
            "limit": limit,
            "confidence_threshold": confidence_threshold
        }
        
        response = await self._make_request(
            "POST", 
            f"classification/versions/{version}/map",
            data=data,
            version=version
        )
        
        result = []
        for mapping in response.get("data", []):
            concept_mapping = ConceptMapping(
                concept=mapping["concept"],
                occupations=[
                    OccupationMapping(
                        id=occ["id"],
                        title=occ["title"],
                        code=occ.get("soc_code", ""),
                        confidence=occ["confidence"],
                        type=occ.get("type")
                    )
                    for occ in mapping.get("occupations", [])
                ]
            )
            result.append(concept_mapping)
        
        return result
    
    async def normalize_job_title(
        self,
        title: str,
        version: str = "latest"
    ) -> TitleNormalizationResult:
        """
        Normalize a job title to standard occupation classification.
        
        Args:
            title: Raw job title to normalize
            version: API version to use
            
        Returns:
            Normalized title with SOC code and confidence
        """
        response = await self._make_request(
            "POST",
            f"classification/versions/{version}/normalize",
            data=title,
            version=version
        )
        
        data = response.get("data", {})
        return TitleNormalizationResult(
            normalized_title=data["normalized_title"],
            soc_code=data["soc_code"],
            confidence=data["confidence"],
            alternatives=data.get("alternatives", [])
        )
    
    async def extract_skills_from_description(
        self,
        description: str,
        confidence_threshold: float = 0.6,
        version: str = "latest"
    ) -> SkillsExtractionResult:
        """
        Extract skills from job description text.
        
        Args:
            description: Job description text
            confidence_threshold: Minimum confidence for skill extraction
            version: API version to use
            
        Returns:
            Extracted skills with confidence scores
        """
        data = {
            "description": description,
            "confidence_threshold": confidence_threshold
        }
        
        response = await self._make_request(
            "POST",
            f"classification/versions/{version}/extract-skills",
            data=data,
            version=version
        )
        
        result_data = response.get("data", {})
        return SkillsExtractionResult(
            extracted_skills=result_data.get("skills", []),
            confidence_scores=result_data.get("confidence_scores", {})
        )
    
    async def classify_occupation_level(
        self,
        occupation_title: str,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Classify occupation by level (entry, mid, senior, etc.).
        
        Args:
            occupation_title: Occupation title to classify
            version: API version to use
            
        Returns:
            Classification with level and confidence
        """
        response = await self._make_request(
            "POST",
            f"classification/versions/{version}/classify-level",
            data={"title": occupation_title},
            version=version
        )
        
        return response.get("data", {})
    
    async def get_occupation_hierarchy(
        self,
        soc_code: str,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Get occupation hierarchy for a SOC code.
        
        Args:
            soc_code: Standard Occupational Classification code
            version: API version to use
            
        Returns:
            Occupation hierarchy information
        """
        response = await self._make_request(
            "GET",
            f"classification/versions/{version}/hierarchy/{soc_code}",
            version=version
        )
        
        return response.get("data", {})
    
    async def search_occupations(
        self,
        query: str,
        limit: int = 20,
        soc_level: Optional[int] = None,
        version: str = "latest"
    ) -> List[Dict[str, Any]]:
        """
        Search occupations by query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            soc_level: SOC classification level (2, 3, 4, 5, 6)
            version: API version to use
            
        Returns:
            List of matching occupations
        """
        params = {
            "q": query,
            "limit": limit
        }
        
        if soc_level:
            params["soc_level"] = soc_level
        
        response = await self._make_request(
            "GET",
            f"classification/versions/{version}/occupations",
            params=params,
            version=version
        )
        
        return response.get("data", [])
    
    async def bulk_classify_concepts(
        self,
        requests: List[BulkClassificationRequest],
        version: str = "latest"
    ) -> List[Dict[str, Any]]:
        """
        Perform bulk classification of multiple concept sets.
        
        Args:
            requests: List of bulk classification requests
            version: API version to use
            
        Returns:
            List of classification results
        """
        data = {
            "requests": [req.model_dump() for req in requests]
        }
        
        response = await self._make_request(
            "POST",
            f"classification/versions/{version}/bulk",
            data=data,
            version=version
        )
        
        return response.get("data", [])
    
    async def get_soc_metadata(
        self,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Get SOC (Standard Occupational Classification) metadata.
        
        Args:
            version: API version to use
            
        Returns:
            SOC classification metadata
        """
        response = await self._make_request(
            "GET",
            f"classification/versions/{version}/soc/meta",
            version=version
        )
        
        return response.get("data", {})
    
    async def validate_soc_code(
        self,
        soc_code: str,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Validate a SOC code and get its details.
        
        Args:
            soc_code: SOC code to validate
            version: API version to use
            
        Returns:
            SOC code validation and details
        """
        response = await self._make_request(
            "GET",
            f"classification/versions/{version}/soc/{soc_code}",
            version=version
        )
        
        return response.get("data", {})
    
    async def get_classification_metadata(
        self,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Get Classification API metadata and version information.
        
        Args:
            version: API version to use
            
        Returns:
            API metadata and version information
        """
        response = await self._make_request(
            "GET",
            f"classification/versions/{version}",
            version=version
        )
        
        return response.get("data", {})