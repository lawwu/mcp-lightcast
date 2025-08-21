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
    confidence: float
    title: TitleDetail
    jobLevels: Optional[List[str]] = None


class TitlesVersionMetadata(BaseModel):
    """Titles version metadata."""
    version: str
    fields: List[str]
    titleCount: int
    removedTitleCount: int


class TitlesGeneralMetadata(BaseModel):
    """General titles metadata."""
    attribution: Dict[str, Any]
    latestVersion: str


class TitlesAPIClient(BaseLightcastClient):
    """Client for Lightcast Titles API."""
    
    def __init__(self):
        super().__init__(api_name="titles")
    
    async def search_titles(
        self,
        query: str,
        limit: int = 10,
        version: str = "5.47"
    ) -> List[TitleSearchResult]:
        """Search for titles by name."""
        params = {
            "q": query,
            "limit": limit
        }
        
        response = await self.get(f"versions/{version}/titles", params=params, version=version)
        return [TitleSearchResult(**item) for item in response.get("data", [])]
    
    async def get_title_by_id(
        self,
        title_id: str,
        version: str = "5.47"
    ) -> TitleDetail:
        """Get detailed information about a specific title."""
        response = await self.get(f"versions/{version}/titles/{title_id}", version=version)
        return TitleDetail(**response.get("data", {}))
    
    async def normalize_title(
        self,
        raw_title: str,
        version: str = "5.47"
    ) -> Dict[str, Any]:
        """Normalize a raw job title string to the best matching Lightcast title."""
        response = await self.post(
            f"versions/{version}/normalize",
            data={"term": raw_title},
            version=version
        )
        return response
    
    async def get_title_hierarchy(
        self,
        title_id: str,
        version: str = "5.47"
    ) -> Dict[str, Any]:
        """Get the hierarchical structure for a title."""
        response = await self.get(f"versions/{version}/titles/{title_id}/hierarchy", version=version)
        return response.get("data", {})
    
    async def get_titles_metadata(
        self,
        version: str = "5.47"
    ) -> Dict[str, Any]:
        """Get metadata about the titles taxonomy."""
        response = await self.get(f"versions/{version}/meta", version=version)
        return response.get("data", {})
    
    async def get_version_metadata(
        self,
        version: str = "5.47"
    ) -> TitlesVersionMetadata:
        """Get comprehensive metadata about a titles version."""
        response = await self.get(f"versions/{version}", version=version)
        return TitlesVersionMetadata(**response.get("data", {}))
    
    async def get_general_metadata(self) -> TitlesGeneralMetadata:
        """Get general titles taxonomy metadata."""
        response = await self.get("meta")
        return TitlesGeneralMetadata(**response.get("data", {}))
    
    async def bulk_retrieve_titles(
        self,
        title_ids: List[str],
        version: str = "5.47"
    ) -> List[TitleDetail]:
        """Retrieve multiple titles by their IDs in a single request."""
        data = {"ids": title_ids}
        response = await self.post(f"versions/{version}/titles", data=data, version=version)
        return [TitleDetail(**item) for item in response.get("data", [])]