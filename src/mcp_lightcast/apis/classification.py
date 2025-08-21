"""Lightcast Classification API client."""

from typing import Any

from pydantic import BaseModel, Field

from .base import BaseLightcastClient


class OccupationMapping(BaseModel):
    """Occupation mapping result."""
    id: str
    title: str
    code: str = Field(alias="soc_code", default="")
    confidence: float
    type: str | None = None


class ConceptMapping(BaseModel):
    """Concept mapping result."""
    concept: str
    occupations: list[OccupationMapping]


class TitleNormalizationResult(BaseModel):
    """Title normalization result."""
    normalized_title: str
    soc_code: str
    confidence: float
    alternatives: list[dict[str, Any]] | None = None


class SkillExtractionResult(BaseModel):
    """Skill extraction result."""
    concept: dict[str, Any]
    confidence: float


class SkillsExtractionResult(BaseModel):
    """Skills extraction result."""
    concepts: list[SkillExtractionResult]
    trace: list[dict[str, Any]] | None = None
    warnings: list[str] | None = None


class BulkClassificationRequest(BaseModel):
    """Bulk classification request."""
    concepts: list[str]
    options: dict[str, Any] | None = None


class ClassificationAPIClient(BaseLightcastClient):
    """Client for Lightcast Classification API."""

    def __init__(self):
        super().__init__(api_name="classification")

    async def get_version_metadata(
        self,
        version: str = "2025.8"
    ) -> dict[str, Any]:
        """
        Get Classification API version metadata.
        
        Args:
            version: API version to use (e.g., '2025.8', '2025.7')
            
        Returns:
            Version metadata information
        """
        response = await self._make_request(
            "GET",
            f"classifications/{version}"
        )

        # Response is the full JSON object from the API
        if isinstance(response, dict):
            data = response.get("data", {})
            if isinstance(data, dict):
                return data
            elif isinstance(data, list) and len(data) > 0:
                return data[0] if isinstance(data[0], dict) else {"items": data}
            else:
                return {"raw_response": data}
        else:
            return {"raw_response": response}

    async def get_available_versions(
        self
    ) -> list[str]:
        """
        Get available Classification API versions.
        
        Returns:
            List of available version numbers
        """
        response = await self._make_request(
            "GET",
            "classifications"
        )

        # Extract versions from the response
        data = response.get("data", [])
        if isinstance(data, list):
            # Extract just the version numbers from the full version objects
            versions = []
            for item in data:
                if isinstance(item, dict) and "release" in item:
                    versions.append(item["release"])
            return versions
        return []

    async def extract_skills_from_text(
        self,
        text: str,
        confidence_threshold: float = 0.6,
        trace: bool = True,
        input_locale: str = "en-US",
        output_locale: str = "en-US",
        version: str = "2025.8"
    ) -> SkillsExtractionResult:
        """
        Extract skills from text using the Classification API.
        
        Args:
            text: Text to extract skills from
            confidence_threshold: Minimum confidence for skill extraction
            trace: Whether to include trace information
            input_locale: Input text locale
            output_locale: Output locale for skill names
            version: API version to use (e.g., '2025.8', '2025.7')
            
        Returns:
            Extracted skills with confidence scores
        """
        data = {
            "text": text,
            "confidenceThreshold": confidence_threshold,
            "trace": trace,
            "inputLocale": input_locale,
            "outputLocale": output_locale
        }

        response = await self._make_request(
            "POST",
            f"classifications/{version}/skills/extract",
            data=data
        )

        # Parse response according to actual API format
        result_data = response.get("data", {})
        warnings = response.get("warnings", [])

        # The data contains concepts, not a direct list
        concepts_data = result_data.get("concepts", [])
        trace_data = result_data.get("trace", [])

        skill_results = []
        for item in concepts_data:
            skill_results.append(SkillExtractionResult(
                concept=item.get("concept", {}),
                confidence=item.get("confidence", 0.0)
            ))

        return SkillsExtractionResult(
            concepts=skill_results,
            trace=trace_data,
            warnings=warnings
        )

    async def get_api_status(
        self
    ) -> dict[str, Any]:
        """
        Get Classification API status.
        
        Returns:
            API status information
        """
        response = await self._make_request(
            "GET",
            "status"
        )

        return response.get("data", {})

    async def get_api_metadata(
        self
    ) -> dict[str, Any]:
        """
        Get Classification API metadata.
        
        Returns:
            API metadata information
        """
        response = await self._make_request(
            "GET",
            "meta"
        )

        return response.get("data", {})

    async def list_skills(
        self,
        version: str = "2025.8",
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List available skills in the classification system.
        
        Args:
            version: API version to use
            limit: Maximum number of skills to return
            offset: Number of skills to skip
            
        Returns:
            List of available skills
        """
        params = {
            "limit": limit,
            "offset": offset
        }

        response = await self._make_request(
            "GET",
            f"classifications/{version}/skills",
            params=params
        )

        return response.get("data", [])

    async def list_titles(
        self,
        version: str = "2025.8",
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List available titles in the classification system.
        
        Args:
            version: API version to use
            limit: Maximum number of titles to return
            offset: Number of titles to skip
            
        Returns:
            List of available titles
        """
        params = {
            "limit": limit,
            "offset": offset
        }

        response = await self._make_request(
            "GET",
            f"classifications/{version}/titles",
            params=params
        )

        return response.get("data", [])

    async def normalize_skill(
        self,
        skill_text: str,
        confidence_threshold: float = 0.6,
        version: str = "2025.8"
    ) -> dict[str, Any]:
        """
        Normalize a skill name to standard classification.
        
        Args:
            skill_text: Skill text to normalize
            confidence_threshold: Minimum confidence for normalization
            version: API version to use
            
        Returns:
            Normalized skill information
        """
        # Send as JSON data
        data = {"text": skill_text}
        response = await self._make_request(
            "POST",
            f"classifications/{version}/skills/normalize",
            data=data
        )

        return response.get("data", {})

    async def normalize_title(
        self,
        title_text: str,
        confidence_threshold: float = 0.6,
        version: str = "2025.8"
    ) -> dict[str, Any]:
        """
        Normalize a job title to standard classification.
        
        Args:
            title_text: Title text to normalize
            confidence_threshold: Minimum confidence for normalization
            version: API version to use
            
        Returns:
            Normalized title information
        """
        # Send as JSON data
        data = {"text": title_text}
        response = await self._make_request(
            "POST",
            f"classifications/{version}/titles/normalize",
            data=data
        )

        return response.get("data", {})

    async def extract_occupations_from_text(
        self,
        text: str,
        confidence_threshold: float = 0.6,
        version: str = "2025.8"
    ) -> list[dict[str, Any]]:
        """
        Extract occupations from text (if available).
        
        Args:
            text: Text to extract occupations from
            confidence_threshold: Minimum confidence for extraction
            version: API version to use
            
        Returns:
            List of extracted occupations
        """
        data = {
            "text": text,
            "confidenceThreshold": confidence_threshold
        }

        response = await self._make_request(
            "POST",
            f"classifications/{version}/occupations/extract",
            data=data
        )

        return response.get("data", [])

    async def get_available_mappings(self) -> dict[str, Any]:
        """
        Get all available mappings from the Classification API.
        
        Returns:
            Dictionary containing all available mappings
        """
        response = await self._make_request(
            "GET",
            "mappings"
        )

        return response.get("data", {})

    async def map_concepts(
        self,
        mapping_name: str,
        id_list: list[str]
    ) -> dict[str, Any]:
        """
        Map taxonomy item IDs using a specific mapping.
        
        Args:
            mapping_name: Name of the mapping to use (e.g., "titles_v5.24.0_lot_v6.20.0")
            id_list: List of taxonomy item IDs to map
            
        Returns:
            Dictionary with mapped IDs
            
        Example:
            mapping = await client.map_concepts(
                "titles_v5.24.0_lot_v6.20.0", 
                ["ET6850661D6AE5FA86"]
            )
        """
        data = {"ids": id_list}

        response = await self._make_request(
            "POST",
            f"mappings/{mapping_name}",
            data=data
        )

        return response

    async def map_title_id_to_lotspecocc_id(
        self,
        title_id: str,
        mapping_name: str = "titles_v5.24.0_lot_v6.20.0"
    ) -> str:
        """
        Map title ID to LOT Specialized Occupation ID.
        
        Args:
            title_id: Title ID to map
            mapping_name: Mapping name to use
            
        Returns:
            LOT Specialized Occupation ID
            
        Raises:
            KeyError: If mapping is not found for the given title ID
        """
        # Mapping from EMSI Titles to LOT Specialized Occupations
        response = await self.map_concepts(mapping_name, [title_id])
        data = response.get("data", {})

        if data and data.get(title_id):
            lotspecocc_id = data[title_id][0]  # Take the first mapped ID
            return lotspecocc_id
        else:
            raise KeyError(f"Lightcast could not find mappings for given title ID: {title_id}")
