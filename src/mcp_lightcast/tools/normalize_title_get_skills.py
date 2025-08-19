"""Combined tool for title normalization and skills mapping workflow."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from src.mcp_lightcast.apis.titles import TitlesAPIClient
from src.mcp_lightcast.apis.classification import ClassificationAPIClient
from src.mcp_lightcast.apis.similarity import SimilarityAPIClient


class NormalizedTitleWithSkills(BaseModel):
    """Result model for normalized title with associated skills."""
    raw_title: str
    normalized_title: Dict[str, Any]
    occupation_mappings: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    workflow_metadata: Dict[str, Any]


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
        skill_type: Optional[str] = None,
        confidence_threshold: float = 0.5,
        version: str = "2023.4"
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
            normalized_title = {
                "id": normalized_result.id,
                "name": normalized_result.name,
                "confidence": normalized_result.confidence,
                "type": normalized_result.type
            }
            
            # Step 2: Map to occupation codes using classification API
            workflow_metadata["steps_completed"].append("occupation_mapping")
            classification_results = await self.classification_client.map_concepts(
                concepts=[normalized_result.name],
                target_taxonomy="onet_soc",
                limit=max_occupations,
                confidence_threshold=confidence_threshold,
                version=version
            )
            
            occupation_mappings = []
            for result in classification_results:
                occupation_mappings.append({
                    "occupation_id": result.mapped_id,
                    "occupation_name": result.mapped_name,
                    "confidence": result.confidence,
                    "mapping_type": result.mapping_type
                })
            
            # Step 3: Get skills for each mapped occupation
            workflow_metadata["steps_completed"].append("skills_extraction")
            all_skills = []
            skills_by_occupation = {}
            
            for occupation in occupation_mappings:
                try:
                    occupation_skills = await self.similarity_client.get_occupation_skills(
                        occupation_id=occupation["occupation_id"],
                        limit=max_skills_per_occupation,
                        skill_type=skill_type,
                        version=version
                    )
                    
                    skills_by_occupation[occupation["occupation_id"]] = occupation_skills.skills
                    all_skills.extend(occupation_skills.skills)
                    
                except Exception as e:
                    workflow_metadata["errors"].append(f"Failed to get skills for {occupation['occupation_id']}: {str(e)}")
            
            # Deduplicate skills by ID
            unique_skills = {}
            for skill in all_skills:
                skill_id = skill.get("id")
                if skill_id and skill_id not in unique_skills:
                    unique_skills[skill_id] = skill
            
            # Add occupation source information to skills
            for skill_id, skill in unique_skills.items():
                skill["source_occupations"] = []
                for occ_id, occ_skills in skills_by_occupation.items():
                    if any(s.get("id") == skill_id for s in occ_skills):
                        occ_info = next((o for o in occupation_mappings if o["occupation_id"] == occ_id), None)
                        if occ_info:
                            skill["source_occupations"].append({
                                "id": occ_id,
                                "name": occ_info["occupation_name"],
                                "confidence": occ_info["confidence"]
                            })
            
            workflow_metadata["steps_completed"].append("workflow_complete")
            workflow_metadata["summary"] = {
                "normalized_title_confidence": normalized_result.confidence,
                "occupation_mappings_count": len(occupation_mappings),
                "unique_skills_count": len(unique_skills),
                "total_skills_before_dedup": len(all_skills)
            }
            
            return NormalizedTitleWithSkills(
                raw_title=raw_title,
                normalized_title=normalized_title,
                occupation_mappings=occupation_mappings,
                skills=list(unique_skills.values()),
                workflow_metadata=workflow_metadata
            )
            
        except Exception as e:
            workflow_metadata["errors"].append(f"Workflow failed: {str(e)}")
            raise
    
    async def get_title_skills_simple(
        self,
        raw_title: str,
        limit: int = 50,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
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