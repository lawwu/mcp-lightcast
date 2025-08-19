"""Lightcast Titles API client."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class TitleSearchResult(BaseModel):
    """Title search result model."""
    id: str
    name: str
    type: Optional[str] = None


class TitleDetail(BaseModel):
    """Detailed title information."""
    id: str
    name: str
    type: Optional[str] = None
    parent: Optional[Dict[str, Any]] = None
    children: Optional[List[Dict[str, Any]]] = None


class TitleNormalizationResult(BaseModel):
    """Title normalization result."""
    id: str
    name: str
    confidence: float
    type: Optional[str] = None


class TitlesAPIClient(BaseLightcastClient):
    """Client for Lightcast Titles API."""
    
    async def search_titles(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        version: str = "2023.4"
    ) -> List[TitleSearchResult]:
        """Search for titles by name."""
        params = {
            "q": query,
            "limit": limit,
            "offset": offset
        }
        
        response = await self.get(f"titles/versions/{version}", params=params, version=version)
        return [TitleSearchResult(**item) for item in response.get("data", [])]
    
    async def get_title_by_id(
        self,
        title_id: str,
        version: str = "2023.4"
    ) -> TitleDetail:
        """Get detailed information about a specific title."""
        response = await self.get(f"titles/versions/{version}/{title_id}", version=version)
        return TitleDetail(**response.get("data", {}))
    
    async def normalize_title(
        self,
        raw_title: str,
        version: str = "2023.4"
    ) -> TitleNormalizationResult:
        """Normalize a raw job title string to the best matching Lightcast title."""
        response = await self.post(
            f"titles/versions/{version}/normalize",
            data=raw_title,
            version=version
        )
        return TitleNormalizationResult(**response.get("data", {}))
    
    async def get_title_hierarchy(
        self,
        title_id: str,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """Get the hierarchical structure for a title."""
        response = await self.get(f"titles/versions/{version}/{title_id}/hierarchy", version=version)
        return response.get("data", {})
    
    async def get_titles_metadata(
        self,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """Get metadata about the titles taxonomy."""
        response = await self.get(f"titles/versions/{version}/meta", version=version)
        return response.get("data", {})