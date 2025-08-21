"""MCP tools for combined Lightcast API workflows."""

from typing import Any

from fastmcp import FastMCP

from .normalize_title_get_skills import TitleNormalizationWorkflow


def register_workflow_tools(mcp: FastMCP):
    """Register workflow-related MCP tools."""

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
            raw_title: Raw job title string to analyze
            max_occupations: Maximum number of occupation mappings to consider (default: 5)
            max_skills_per_occupation: Maximum skills to retrieve per occupation (default: 20)
            skill_type: Filter skills by type (e.g., "Hard Skill", "Soft Skill") (optional)
            confidence_threshold: Minimum confidence for occupation mappings (default: 0.5)
            version: API version to use (default: "2023.4")
            
        Returns:
            Complete workflow results including normalized title, occupation mappings, and skills
        """
        async with TitleNormalizationWorkflow() as workflow:
            result = await workflow.normalize_title_and_get_skills(
                raw_title=raw_title,
                max_occupations=max_occupations,
                max_skills_per_occupation=max_skills_per_occupation,
                skill_type=skill_type,
                confidence_threshold=confidence_threshold,
                version=version
            )

            return {
                "raw_title": result.raw_title,
                "normalized_title": result.normalized_title,
                "occupation_mappings": result.occupation_mappings,
                "skills": result.skills,
                "metadata": result.workflow_metadata
            }

    @mcp.tool
    async def get_title_skills_simple(
        raw_title: str,
        limit: int = 50,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Simplified workflow to get skills for a job title.
        
        Returns just the essential information: normalized title and associated skills.
        
        Args:
            raw_title: Raw job title string to analyze
            limit: Maximum number of skills to return (default: 50)
            version: API version to use (default: "2023.4")
            
        Returns:
            Simplified results with normalized title and skills list
        """
        async with TitleNormalizationWorkflow() as workflow:
            return await workflow.get_title_skills_simple(
                raw_title=raw_title,
                limit=limit,
                version=version
            )

    @mcp.tool
    async def analyze_job_posting_skills(
        job_title: str,
        job_description: str = "",
        extract_from_description: bool = True,
        merge_results: bool = True,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Analyze a job posting to identify relevant skills from both title and description.
        
        Args:
            job_title: Job title to analyze
            job_description: Job description text (optional)
            extract_from_description: Whether to extract skills from description text (default: True)
            merge_results: Whether to merge title-based and description-based skills (default: True)
            version: API version to use (default: "2023.4")
            
        Returns:
            Combined analysis of skills from title normalization and description extraction
        """
        from src.mcp_lightcast.apis.skills import SkillsAPIClient

        results = {
            "job_title": job_title,
            "job_description_length": len(job_description),
            "title_based_skills": [],
            "description_extracted_skills": [],
            "merged_skills": [],
            "analysis_metadata": {}
        }

        # Get skills from title normalization workflow
        async with TitleNormalizationWorkflow() as workflow:
            title_result = await workflow.get_title_skills_simple(
                raw_title=job_title,
                limit=30,
                version=version
            )

            results["title_based_skills"] = title_result["skills"]
            results["normalized_title"] = title_result["normalized_title"]
            results["title_confidence"] = title_result["confidence"]

        # Extract skills from job description if provided
        if job_description and extract_from_description:
            async with SkillsAPIClient() as skills_client:
                extracted = await skills_client.extract_skills_from_text(
                    text=job_description,
                    confidence_threshold=0.5,
                    version=version
                )
                results["description_extracted_skills"] = extracted

        # Merge results if requested
        if merge_results:
            all_skills = {}

            # Add title-based skills
            for skill in results["title_based_skills"]:
                skill_name = skill.get("name", "")
                if skill_name:
                    all_skills[skill_name] = {
                        **skill,
                        "sources": ["title_normalization"]
                    }

            # Add description-extracted skills
            for skill in results["description_extracted_skills"]:
                skill_name = skill.get("name", skill.get("skill_name", ""))
                if skill_name:
                    if skill_name in all_skills:
                        all_skills[skill_name]["sources"].append("description_extraction")
                        # Update confidence if description extraction has higher confidence
                        desc_confidence = skill.get("confidence", 0)
                        if desc_confidence > all_skills[skill_name].get("confidence", 0):
                            all_skills[skill_name]["confidence"] = desc_confidence
                    else:
                        all_skills[skill_name] = {
                            **skill,
                            "sources": ["description_extraction"]
                        }

            results["merged_skills"] = list(all_skills.values())
            results["analysis_metadata"] = {
                "title_skills_count": len(results["title_based_skills"]),
                "description_skills_count": len(results["description_extracted_skills"]),
                "merged_skills_count": len(results["merged_skills"]),
                "unique_skills_from_both_sources": len([
                    s for s in results["merged_skills"]
                    if len(s.get("sources", [])) > 1
                ])
            }

        return results
