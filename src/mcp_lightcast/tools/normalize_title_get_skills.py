"""Combined tool for title normalization and skills mapping workflow."""

from typing import Any

from pydantic import BaseModel

from ..apis.classification import ClassificationAPIClient
from ..apis.similarity import SimilarityAPIClient
from ..apis.titles import TitlesAPIClient


class NormalizedTitleWithSkills(BaseModel):
    """Result model for normalized title with associated skills."""
    raw_title: str
    normalized_title: dict[str, Any]
    occupation_mappings: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    workflow_metadata: dict[str, Any]


class TitleNormalizationWorkflow:
    """Workflow for normalizing titles and getting associated skills."""

    def __init__(self):
        self.titles_client = TitlesAPIClient()
        self.classification_client = ClassificationAPIClient()
        self.similarity_client = SimilarityAPIClient()

    async def __aenter__(self):
        await self.titles_client.__aenter__()
        await self.classification_client.__aenter__()
        await self.similarity_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.titles_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.classification_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.similarity_client.__aexit__(exc_type, exc_val, exc_tb)

    async def normalize_title_and_get_skills(
        self,
        raw_title: str,
        max_occupations: int = 5,
        max_skills_per_occupation: int = 20,
        skill_type: str | None = None,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> NormalizedTitleWithSkills:
        """
        Complete workflow: normalize title → map to occupations → get skills.
        
        Args:
            raw_title: Raw job title string to normalize
            max_occupations: Maximum number of occupation mappings to return
            max_skills_per_occupation: Maximum skills to get per occupation
            skill_type: Filter skills by type (e.g., 'Hard Skill', 'Soft Skill')
            confidence_threshold: Minimum confidence for classification mappings
            version: API version to use
            
        Returns:
            NormalizedTitleWithSkills object with complete workflow results
        """
        workflow_metadata = {
            "steps_completed": [],
            "errors": [],
            "processing_time": {}
        }

        try:
            # Step 1: Normalize the title
            workflow_metadata["steps_completed"].append("title_normalization")
            normalized_result = await self.titles_client.normalize_title(raw_title, version)
            # Handle the actual dict structure returned by the API
            result_data = normalized_result.get("data", normalized_result)
            normalized_title = {
                "id": result_data["title"]["id"],
                "name": result_data["title"]["name"],
                "confidence": result_data["confidence"],
                "type": result_data["title"].get("type")  # type might not always be present
            }

            # Step 2: Extract skills from title text using classification API
            workflow_metadata["steps_completed"].append("skills_extraction") 
            try:
                extracted_skills = await self.classification_client.extract_skills_from_text(
                    result_data["title"]["name"]
                )
                
                # Convert to simple list format
                skills_list = []
                for skill_result in extracted_skills.concepts:
                    skills_list.append({
                        "id": skill_result.concept["id"],
                        "name": skill_result.concept["name"],
                        "confidence": skill_result.confidence,
                        "type": skill_result.concept.get("skillType", "Unknown")
                    })
                    
                workflow_metadata["steps_completed"].append("workflow_complete")
                workflow_metadata["summary"] = {
                    "normalized_title_confidence": result_data["confidence"],
                    "skills_count": len(skills_list)
                }
                
            except Exception as e:
                workflow_metadata["errors"].append(f"Failed to extract skills: {str(e)}")
                skills_list = []

            return NormalizedTitleWithSkills(
                raw_title=raw_title,
                normalized_title=normalized_title,
                occupation_mappings=[],  # Simplified - no occupation mapping
                skills=skills_list,
                workflow_metadata=workflow_metadata
            )

        except Exception as e:
            workflow_metadata["errors"].append(f"Workflow failed: {str(e)}")
            raise

    async def get_title_skills_simple(
        self,
        raw_title: str,
        limit: int = 50,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Simplified version that returns just the essential information.
        """
        result = await self.normalize_title_and_get_skills(
            raw_title=raw_title,
            max_occupations=3,
            max_skills_per_occupation=limit // 3,
            version=version
        )

        return {
            "normalized_title": result.normalized_title["name"],
            "confidence": result.normalized_title["confidence"],
            "top_occupations": [occ["occupation_name"] for occ in result.occupation_mappings[:3]],
            "skills": [
                {
                    "name": skill.get("name"),
                    "type": skill.get("type"),
                    "category": skill.get("category")
                }
                for skill in result.skills[:limit]
            ],
            "skills_count": len(result.skills)
        }
