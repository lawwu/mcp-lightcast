"""MCP tools for Lightcast Career Pathways API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.career_pathways import CareerPathwaysAPIClient


def register_career_pathways_tools(mcp: FastMCP):
    """Register all career pathways-related MCP tools."""

    @mcp.tool
    async def analyze_career_pathway(
        from_occupation_id: str,
        to_occupation_id: str,
        max_steps: int = 3,
        include_skill_analysis: bool = True,
        region: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Analyze career pathway between two occupations.
        
        Args:
            from_occupation_id: Starting occupation ID
            to_occupation_id: Target occupation ID
            max_steps: Maximum number of intermediate steps (default: 3)
            include_skill_analysis: Include skill gap analysis (default: True)
            region: Geographic region for analysis
            version: API version to use (default: "latest")
            
        Returns:
            Career pathway analysis
        """
        async with CareerPathwaysAPIClient() as client:
            result = await client.analyze_career_pathway(from_occupation_id, to_occupation_id, max_steps, include_skill_analysis, region, version)
            return {
                "from_occupation_id": result.from_occupation_id,
                "to_occupation_id": result.to_occupation_id,
                "pathways": [
                    {
                        "pathway_id": pathway.pathway_id,
                        "pathway_name": pathway.pathway_name,
                        "starting_occupation": {
                            "occupation_id": pathway.starting_occupation.occupation_id,
                            "occupation_title": pathway.starting_occupation.occupation_title,
                            "soc_code": pathway.starting_occupation.soc_code,
                            "step_order": pathway.starting_occupation.step_order
                        } if pathway.starting_occupation else None,
                        "target_occupation": {
                            "occupation_id": pathway.target_occupation.occupation_id,
                            "occupation_title": pathway.target_occupation.occupation_title,
                            "soc_code": pathway.target_occupation.soc_code,
                            "step_order": pathway.target_occupation.step_order
                        } if pathway.target_occupation else None,
                        "intermediate_steps": [
                            {
                                "occupation_id": step.occupation_id,
                                "occupation_title": step.occupation_title,
                                "soc_code": step.soc_code,
                                "step_order": step.step_order,
                                "transition_probability": step.transition_probability,
                                "median_duration": step.median_duration
                            }
                            for step in pathway.intermediate_steps
                        ],
                        "total_duration": pathway.total_duration,
                        "difficulty_score": pathway.difficulty_score,
                        "success_rate": pathway.success_rate
                    }
                    for pathway in result.pathways
                ],
                "skill_gaps": [
                    {
                        "skill_id": gap.skill_id,
                        "skill_name": gap.skill_name,
                        "gap_type": gap.gap_type,
                        "importance": gap.importance,
                        "training_time": gap.training_time
                    }
                    for gap in result.skill_gaps
                ],
                "recommended_training": result.recommended_training
            }

    @mcp.tool
    async def discover_career_pathways(
        occupation_id: str,
        pathway_type: str = "advancement",
        career_level: str | None = None,
        industry_filter: list[str] | None = None,
        limit: int = 20,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Discover potential career pathways from a given occupation.
        
        Args:
            occupation_id: Starting occupation ID
            pathway_type: Type of pathway (advancement, lateral, transition) (default: "advancement")
            career_level: Target career level (entry, mid, senior, executive)
            industry_filter: Filter by target industries
            limit: Maximum number of pathways (default: 20)
            version: API version to use (default: "latest")
            
        Returns:
            List of discovered career pathways
        """
        async with CareerPathwaysAPIClient() as client:
            results = await client.discover_career_pathways(occupation_id, pathway_type, career_level, industry_filter, limit, version)
            return [
                {
                    "pathway_id": pathway.pathway_id,
                    "pathway_name": pathway.pathway_name,
                    "starting_occupation": {
                        "occupation_id": pathway.starting_occupation.occupation_id,
                        "occupation_title": pathway.starting_occupation.occupation_title,
                        "soc_code": pathway.starting_occupation.soc_code
                    } if pathway.starting_occupation else None,
                    "target_occupation": {
                        "occupation_id": pathway.target_occupation.occupation_id,
                        "occupation_title": pathway.target_occupation.occupation_title,
                        "soc_code": pathway.target_occupation.soc_code
                    } if pathway.target_occupation else None,
                    "intermediate_steps": [
                        {
                            "occupation_id": step.occupation_id,
                            "occupation_title": step.occupation_title,
                            "step_order": step.step_order,
                            "transition_probability": step.transition_probability
                        }
                        for step in pathway.intermediate_steps
                    ],
                    "total_duration": pathway.total_duration,
                    "difficulty_score": pathway.difficulty_score,
                    "success_rate": pathway.success_rate
                }
                for pathway in results
            ]

    @mcp.tool
    async def get_skill_transition_map(
        from_occupation_id: str,
        to_occupation_id: str,
        skill_level: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get detailed skill transition mapping between occupations.
        
        Args:
            from_occupation_id: Starting occupation ID
            to_occupation_id: Target occupation ID
            skill_level: Skill level filter (basic, intermediate, advanced)
            version: API version to use (default: "latest")
            
        Returns:
            Skill transition mapping data
        """
        async with CareerPathwaysAPIClient() as client:
            return await client.get_skill_transition_map(from_occupation_id, to_occupation_id, skill_level, version)

    @mcp.tool
    async def analyze_industry_transitions(
        from_industry_ids: list[str] | None = None,
        to_industry_ids: list[str] | None = None,
        time_period: str | None = None,
        region: str | None = None,
        limit: int = 50,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Analyze career transitions between industries.
        
        Args:
            from_industry_ids: Source industry IDs
            to_industry_ids: Target industry IDs
            time_period: Time period for analysis
            region: Geographic region
            limit: Maximum number of results (default: 50)
            version: API version to use (default: "latest")
            
        Returns:
            List of industry transitions
        """
        async with CareerPathwaysAPIClient() as client:
            results = await client.analyze_industry_transitions(from_industry_ids, to_industry_ids, time_period, region, limit, version)
            return [
                {
                    "from_industry_id": transition.from_industry_id,
                    "to_industry_id": transition.to_industry_id,
                    "from_industry_name": transition.from_industry_name,
                    "to_industry_name": transition.to_industry_name,
                    "transition_volume": transition.transition_volume,
                    "success_rate": transition.success_rate,
                    "median_salary_change": transition.median_salary_change
                }
                for transition in results
            ]

    @mcp.tool
    async def get_pathway_recommendations(
        current_occupation_id: str,
        career_goals: list[str],
        skills_inventory: list[str] | None = None,
        time_horizon: int | None = None,
        region: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get personalized career pathway recommendations.
        
        Args:
            current_occupation_id: Current occupation ID
            career_goals: List of career goals (salary_increase, advancement, industry_change)
            skills_inventory: Current skills list
            time_horizon: Time horizon for career planning (months)
            region: Geographic region
            version: API version to use (default: "latest")
            
        Returns:
            Personalized pathway recommendations
        """
        async with CareerPathwaysAPIClient() as client:
            return await client.get_pathway_recommendations(current_occupation_id, career_goals, skills_inventory, time_horizon, region, version)

    @mcp.tool
    async def validate_pathway_feasibility(
        pathway_steps: list[str],
        constraints: dict[str, Any] | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Validate the feasibility of a custom career pathway.
        
        Args:
            pathway_steps: List of occupation IDs in pathway order
            constraints: Pathway constraints (time, location, education, etc.)
            version: API version to use (default: "latest")
            
        Returns:
            Pathway feasibility analysis
        """
        async with CareerPathwaysAPIClient() as client:
            return await client.validate_pathway_feasibility(pathway_steps, constraints, version)

    @mcp.tool
    async def get_trending_pathways(
        industry_id: str | None = None,
        region: str | None = None,
        time_period: str | None = None,
        limit: int = 20,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get trending career pathways based on recent data.
        
        Args:
            industry_id: Filter by industry
            region: Geographic region
            time_period: Time period for trend analysis
            limit: Maximum number of results (default: 20)
            version: API version to use (default: "latest")
            
        Returns:
            List of trending pathways
        """
        async with CareerPathwaysAPIClient() as client:
            return await client.get_trending_pathways(industry_id, region, time_period, limit, version)

    @mcp.tool
    async def get_pathways_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Career Pathways API metadata and version information.
        
        Args:
            version: API version to use (default: "latest")
            
        Returns:
            API metadata and version information
        """
        async with CareerPathwaysAPIClient() as client:
            return await client.get_pathways_metadata(version)
