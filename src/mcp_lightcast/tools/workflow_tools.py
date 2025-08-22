"""MCP tools for combined Lightcast API workflows."""

from typing import Any

from fastmcp import FastMCP

from .normalize_title_get_skills import TitleNormalizationWorkflow
from ..apis.skills import SkillsAPIClient
from ..apis.classification import ClassificationAPIClient


def register_workflow_tools(mcp: FastMCP):
    """Register core workflow-related MCP tools."""

    @mcp.tool
    async def normalize_title_and_get_skills(
        raw_title: str,
        max_occupations: int = 5,
        max_skills_per_occupation: int = 20,
        skill_type: str | None = None,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Complete workflow: normalize a job title and get associated skills.
        
        This tool performs the following steps:
        1. Normalizes the raw job title using Lightcast's title normalization
        2. Maps the normalized title to occupation codes using classification API
        3. Retrieves skills associated with those occupations using similarity API
        
        Args:
            raw_title: Raw job title text to normalize and analyze
            max_occupations: Maximum number of occupations to retrieve (default: 5)
            max_skills_per_occupation: Maximum skills per occupation (default: 20)
            skill_type: Filter skills by type (e.g., "Hard Skill", "Soft Skill")
            confidence_threshold: Minimum confidence for skill extraction (default: 0.5)
            version: API version to use (default: "latest")
            
        Returns:
            Complete workflow results with normalized title and associated skills
        """
        async with TitleNormalizationWorkflow() as workflow:
            return await workflow.normalize_title_and_get_skills(
                raw_title, max_occupations, max_skills_per_occupation, 
                skill_type, confidence_threshold, version
            )

    @mcp.tool
    async def analyze_job_posting_skills(
        job_title: str,
        job_description: str,
        extract_from_description: bool = True,
        confidence_threshold: float = 0.5,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Comprehensive analysis of skills mentioned in a job posting.
        
        Combines title normalization and text extraction to provide complete
        skills analysis for job postings.
        
        Args:
            job_title: Job title from posting
            job_description: Full job description text
            extract_from_description: Whether to extract skills from description text
            confidence_threshold: Minimum confidence for skill extraction (default: 0.5)
            version: API version to use (default: "latest")
            
        Returns:
            Combined skills analysis from both title and description
        """
        results = {
            "job_title": job_title,
            "title_skills": [],
            "description_skills": [],
            "combined_skills": []
        }
        
        # Get skills from title normalization
        async with TitleNormalizationWorkflow() as workflow:
            title_result = await workflow.get_title_skills_simple(job_title, limit=10, version=version)
            results["title_skills"] = title_result.get("skills", [])
        
        # Extract skills from description if requested
        if extract_from_description and job_description:
            async with SkillsAPIClient() as client:
                description_skills = await client.extract_skills_from_text(
                    job_description, confidence_threshold, version
                )
                results["description_skills"] = description_skills
        
        # Combine and deduplicate skills
        all_skills = {}
        for skill in results["title_skills"] + results["description_skills"]:
            skill_id = skill.get("id") or skill.get("skill", {}).get("id")
            if skill_id and skill_id not in all_skills:
                all_skills[skill_id] = skill
        
        results["combined_skills"] = list(all_skills.values())
        results["total_unique_skills"] = len(all_skills)
        
        return results

    @mcp.tool
    async def normalize_title_and_extract_skills(
        title: str,
        confidence_threshold: float = 0.6,
        version: str = "2025.8"
    ) -> dict[str, Any]:
        """
        Alternative workflow using Classification API for skills extraction.
        
        Uses the Classification API's skills extraction instead of the 
        similarity-based approach for different results.
        
        Args:
            title: Job title to normalize and extract skills for
            confidence_threshold: Minimum confidence for extraction (default: 0.6)
            version: Classification API version (default: "2025.8")
            
        Returns:
            Skills extracted using Classification API approach
        """
        async with ClassificationAPIClient() as client:
            result = await client.extract_skills_from_text(
                f"Job title: {title}", confidence_threshold, version=version
            )
            
            return {
                "title": title,
                "extraction_method": "classification_api",
                "skills": result.concepts if hasattr(result, 'concepts') else [],
                "total_skills": len(result.concepts) if hasattr(result, 'concepts') else 0,
                "confidence_threshold": confidence_threshold
            }