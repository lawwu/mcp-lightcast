"""MCP tools for Lightcast Classification API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.classification import ClassificationAPIClient


def register_classification_tools(mcp: FastMCP):
    """Register all classification-related MCP tools."""

    @mcp.tool
    async def map_concepts_to_occupations(
        concepts: list[str],
        limit: int = 10,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Map concepts to relevant occupations using the Classification API.
        
        Args:
            concepts: List of concepts/job titles to map
            limit: Maximum number of occupations per concept (default: 10)
            confidence_threshold: Minimum confidence score (default: 0.5)
            version: API version to use (default: "latest")
            
        Returns:
            List of concept mappings with occupations
        """
        async with ClassificationAPIClient() as client:
            results = await client.map_concepts_to_occupations(concepts, limit, confidence_threshold, version)
            return [
                {
                    "concept": result.concept,
                    "occupations": [
                        {
                            "id": occ.id,
                            "title": occ.title,
                            "soc_code": occ.code,
                            "confidence": occ.confidence,
                            "type": occ.type
                        }
                        for occ in result.occupations
                    ]
                }
                for result in results
            ]

    @mcp.tool
    async def normalize_job_title(
        title: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Normalize a job title to standard occupation classification.
        
        Args:
            title: Raw job title to normalize
            version: API version to use (default: "latest")
            
        Returns:
            Normalized title with SOC code and confidence
        """
        async with ClassificationAPIClient() as client:
            result = await client.normalize_job_title(title, version)
            return {
                "normalized_title": result.normalized_title,
                "soc_code": result.soc_code,
                "confidence": result.confidence,
                "alternatives": result.alternatives
            }

    @mcp.tool
    async def extract_skills_from_description(
        description: str,
        confidence_threshold: float = 0.6,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Extract skills from job description text using Classification API.
        
        Args:
            description: Job description text
            confidence_threshold: Minimum confidence for skill extraction (default: 0.6)
            version: API version to use (default: "latest")
            
        Returns:
            Extracted skills with confidence scores
        """
        async with ClassificationAPIClient() as client:
            result = await client.extract_skills_from_description(description, confidence_threshold, version)
            return {
                "extracted_skills": result.extracted_skills,
                "confidence_scores": result.confidence_scores
            }

    @mcp.tool
    async def classify_occupation_level(
        occupation_title: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Classify occupation by level (entry, mid, senior, etc.).
        
        Args:
            occupation_title: Occupation title to classify
            version: API version to use (default: "latest")
            
        Returns:
            Classification with level and confidence
        """
        async with ClassificationAPIClient() as client:
            return await client.classify_occupation_level(occupation_title, version)

    @mcp.tool
    async def get_occupation_hierarchy(
        soc_code: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get occupation hierarchy for a SOC code.
        
        Args:
            soc_code: Standard Occupational Classification code
            version: API version to use (default: "latest")
            
        Returns:
            Occupation hierarchy information
        """
        async with ClassificationAPIClient() as client:
            return await client.get_occupation_hierarchy(soc_code, version)

    @mcp.tool
    async def search_occupations(
        query: str,
        limit: int = 20,
        soc_level: int | None = None,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Search occupations by query.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 20)
            soc_level: SOC classification level (2, 3, 4, 5, 6)
            version: API version to use (default: "latest")
            
        Returns:
            List of matching occupations
        """
        async with ClassificationAPIClient() as client:
            return await client.search_occupations(query, limit, soc_level, version)

    @mcp.tool
    async def validate_soc_code(
        soc_code: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Validate a SOC code and get its details.
        
        Args:
            soc_code: SOC code to validate
            version: API version to use (default: "latest")
            
        Returns:
            SOC code validation and details
        """
        async with ClassificationAPIClient() as client:
            return await client.validate_soc_code(soc_code, version)

    @mcp.tool
    async def get_soc_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get SOC (Standard Occupational Classification) metadata.
        
        Args:
            version: API version to use (default: "latest")
            
        Returns:
            SOC classification metadata
        """
        async with ClassificationAPIClient() as client:
            return await client.get_soc_metadata(version)

    @mcp.tool
    async def get_classification_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Classification API metadata and version information.
        
        Args:
            version: API version to use (default: "latest")
            
        Returns:
            API metadata and version information
        """
        async with ClassificationAPIClient() as client:
            return await client.get_classification_metadata(version)
