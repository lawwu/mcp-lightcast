"""Lightcast Career Pathways API client."""

from typing import Any

from pydantic import BaseModel

from .base import BaseLightcastClient


class CareerStep(BaseModel):
    """Career step model."""
    occupation_id: str
    occupation_title: str
    soc_code: str | None = None
    step_order: int
    transition_probability: float | None = None
    required_skills: list[str] | None = None
    median_duration: int | None = None  # months


class CareerPathway(BaseModel):
    """Career pathway model."""
    pathway_id: str
    pathway_name: str
    starting_occupation: CareerStep
    target_occupation: CareerStep
    intermediate_steps: list[CareerStep]
    total_duration: int | None = None  # months
    difficulty_score: float | None = None
    success_rate: float | None = None


class SkillGap(BaseModel):
    """Skill gap model."""
    skill_id: str
    skill_name: str
    gap_type: str  # "missing", "upgrade", "new"
    importance: float
    training_time: int | None = None  # hours


class PathwayAnalysis(BaseModel):
    """Pathway analysis result."""
    from_occupation_id: str
    to_occupation_id: str
    pathways: list[CareerPathway]
    skill_gaps: list[SkillGap]
    recommended_training: list[dict[str, Any]] | None = None


class IndustryTransition(BaseModel):
    """Industry transition model."""
    from_industry_id: str
    to_industry_id: str
    from_industry_name: str
    to_industry_name: str
    transition_volume: int
    success_rate: float
    median_salary_change: float | None = None


class CareerPathwaysAPIClient(BaseLightcastClient):
    """Client for Lightcast Career Pathways API."""

    def __init__(self):
        super().__init__(api_name="career_pathways")

    # Working endpoints discovered from testing
    async def get_api_metadata(self) -> dict[str, Any]:
        """
        Get comprehensive API metadata including model versions and supported taxonomies.
        
        Returns:
            API metadata with dimensions, transition categories, regions, and versions
        """
        response = await self.get("meta")
        return response.get("data", {})

    async def get_api_status(self) -> dict[str, Any]:
        """
        Get API health status.
        
        Returns:
            API health status information
        """
        response = await self.get("status")
        return response.get("data", {})

    async def get_api_documentation(self) -> str:
        """
        Get API documentation.
        
        Returns:
            API documentation content
        """
        response = await self.get("docs")
        return response if isinstance(response, str) else str(response)

    async def get_available_dimensions(self) -> list[str]:
        """
        Get list of available dimensions (taxonomies).
        
        Returns:
            List of available dimension names (soc, onet, lotocc, lotspecocc)
        """
        response = await self.get("dimensions")
        return response.get("data", [])

    async def get_dimension_info(
        self,
        dimension: str
    ) -> dict[str, Any]:
        """
        Get information about a specific dimension (taxonomy).
        
        Args:
            dimension: Dimension ID (soc, onet, lotocc, lotspecocc)
            
        Returns:
            Dimension information including title, description, and taxonomy versions
        """
        response = await self.get(f"dimensions/{dimension}")
        return response.get("data", {})

    async def get_soc_dimension(self) -> dict[str, Any]:
        """Get SOC (Standard Occupation Classification) dimension information."""
        return await self.get_dimension_info("soc")

    async def get_onet_dimension(self) -> dict[str, Any]:
        """Get O*NET dimension information."""
        return await self.get_dimension_info("onet")

    async def get_lotocc_dimension(self) -> dict[str, Any]:
        """Get LOT Occupation dimension information."""
        return await self.get_dimension_info("lotocc")

    async def get_lotspecocc_dimension(self) -> dict[str, Any]:
        """Get LOT Specialized Occupation dimension information."""
        return await self.get_dimension_info("lotspecocc")

    async def analyze_career_pathway(
        self,
        from_occupation_id: str,
        to_occupation_id: str,
        max_steps: int = 3,
        include_skill_analysis: bool = True,
        region: str | None = None,
        version: str = "latest"
    ) -> PathwayAnalysis:
        """
        Analyze career pathway between two occupations.
        
        Args:
            from_occupation_id: Starting occupation ID
            to_occupation_id: Target occupation ID
            max_steps: Maximum number of intermediate steps
            include_skill_analysis: Include skill gap analysis
            region: Geographic region for analysis
            version: API version to use
            
        Returns:
            Career pathway analysis
        """
        data = {
            "from_occupation": from_occupation_id,
            "to_occupation": to_occupation_id,
            "max_steps": max_steps,
            "include_skills": include_skill_analysis
        }
        if region:
            data["region"] = region

        response = await self.post(
            f"pathways/versions/{version}/analyze",
            data=data,
            version=version
        )

        result_data = response.get("data", {})

        # Parse pathways
        pathways = []
        for pathway_data in result_data.get("pathways", []):
            steps = []
            for step_data in pathway_data.get("steps", []):
                steps.append(CareerStep(
                    occupation_id=step_data["occupation_id"],
                    occupation_title=step_data["title"],
                    soc_code=step_data.get("soc_code"),
                    step_order=step_data["order"],
                    transition_probability=step_data.get("probability"),
                    required_skills=step_data.get("required_skills"),
                    median_duration=step_data.get("duration_months")
                ))

            pathways.append(CareerPathway(
                pathway_id=pathway_data["id"],
                pathway_name=pathway_data["name"],
                starting_occupation=steps[0] if steps else None,
                target_occupation=steps[-1] if steps else None,
                intermediate_steps=steps[1:-1] if len(steps) > 2 else [],
                total_duration=pathway_data.get("total_duration"),
                difficulty_score=pathway_data.get("difficulty"),
                success_rate=pathway_data.get("success_rate")
            ))

        # Parse skill gaps
        skill_gaps = []
        for gap_data in result_data.get("skill_gaps", []):
            skill_gaps.append(SkillGap(
                skill_id=gap_data["skill_id"],
                skill_name=gap_data["skill_name"],
                gap_type=gap_data["gap_type"],
                importance=gap_data["importance"],
                training_time=gap_data.get("training_hours")
            ))

        return PathwayAnalysis(
            from_occupation_id=from_occupation_id,
            to_occupation_id=to_occupation_id,
            pathways=pathways,
            skill_gaps=skill_gaps,
            recommended_training=result_data.get("training_recommendations")
        )

    async def discover_career_pathways(
        self,
        occupation_id: str,
        pathway_type: str = "advancement",
        career_level: str | None = None,
        industry_filter: list[str] | None = None,
        limit: int = 20,
        version: str = "latest"
    ) -> list[CareerPathway]:
        """
        Discover potential career pathways from a given occupation.
        
        Args:
            occupation_id: Starting occupation ID
            pathway_type: Type of pathway (advancement, lateral, transition)
            career_level: Target career level (entry, mid, senior, executive)
            industry_filter: Filter by target industries
            limit: Maximum number of pathways
            version: API version to use
            
        Returns:
            List of discovered career pathways
        """
        params = {
            "pathway_type": pathway_type,
            "limit": limit
        }
        if career_level:
            params["career_level"] = career_level
        if industry_filter:
            params["industries"] = ",".join(industry_filter)

        response = await self.get(
            f"pathways/versions/{version}/occupations/{occupation_id}/discover",
            params=params,
            version=version
        )

        pathways = []
        for pathway_data in response.get("data", []):
            # Create career steps
            steps = []
            for step_data in pathway_data.get("steps", []):
                steps.append(CareerStep(
                    occupation_id=step_data["occupation_id"],
                    occupation_title=step_data["title"],
                    soc_code=step_data.get("soc_code"),
                    step_order=step_data["order"],
                    transition_probability=step_data.get("probability"),
                    required_skills=step_data.get("required_skills"),
                    median_duration=step_data.get("duration_months")
                ))

            pathways.append(CareerPathway(
                pathway_id=pathway_data["id"],
                pathway_name=pathway_data["name"],
                starting_occupation=steps[0] if steps else None,
                target_occupation=steps[-1] if steps else None,
                intermediate_steps=steps[1:-1] if len(steps) > 2 else [],
                total_duration=pathway_data.get("total_duration"),
                difficulty_score=pathway_data.get("difficulty"),
                success_rate=pathway_data.get("success_rate")
            ))

        return pathways

    async def get_skill_transition_map(
        self,
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
            version: API version to use
            
        Returns:
            Skill transition mapping data
        """
        params = {}
        if skill_level:
            params["skill_level"] = skill_level

        response = await self.get(
            f"pathways/versions/{version}/skills/transition/{from_occupation_id}/{to_occupation_id}",
            params=params,
            version=version
        )
        return response.get("data", {})

    async def analyze_industry_transitions(
        self,
        from_industry_ids: list[str] | None = None,
        to_industry_ids: list[str] | None = None,
        time_period: str | None = None,
        region: str | None = None,
        limit: int = 50,
        version: str = "latest"
    ) -> list[IndustryTransition]:
        """
        Analyze career transitions between industries.
        
        Args:
            from_industry_ids: Source industry IDs
            to_industry_ids: Target industry IDs
            time_period: Time period for analysis
            region: Geographic region
            limit: Maximum number of results
            version: API version to use
            
        Returns:
            List of industry transitions
        """
        data = {"limit": limit}
        if from_industry_ids:
            data["from_industries"] = from_industry_ids
        if to_industry_ids:
            data["to_industries"] = to_industry_ids
        if time_period:
            data["time_period"] = time_period
        if region:
            data["region"] = region

        response = await self.post(
            f"pathways/versions/{version}/industries/transitions",
            data=data,
            version=version
        )

        transitions = []
        for item in response.get("data", []):
            transitions.append(IndustryTransition(
                from_industry_id=item["from_industry_id"],
                to_industry_id=item["to_industry_id"],
                from_industry_name=item["from_industry_name"],
                to_industry_name=item["to_industry_name"],
                transition_volume=item["volume"],
                success_rate=item["success_rate"],
                median_salary_change=item.get("salary_change")
            ))

        return transitions

    async def get_pathway_recommendations(
        self,
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
            version: API version to use
            
        Returns:
            Personalized pathway recommendations
        """
        data = {
            "current_occupation": current_occupation_id,
            "career_goals": career_goals
        }
        if skills_inventory:
            data["current_skills"] = skills_inventory
        if time_horizon:
            data["time_horizon"] = time_horizon
        if region:
            data["region"] = region

        response = await self.post(
            f"pathways/versions/{version}/recommendations",
            data=data,
            version=version
        )
        return response.get("data", {})

    async def validate_pathway_feasibility(
        self,
        pathway_steps: list[str],
        constraints: dict[str, Any] | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Validate the feasibility of a custom career pathway.
        
        Args:
            pathway_steps: List of occupation IDs in pathway order
            constraints: Pathway constraints (time, location, education, etc.)
            version: API version to use
            
        Returns:
            Pathway feasibility analysis
        """
        data = {"pathway_steps": pathway_steps}
        if constraints:
            data["constraints"] = constraints

        response = await self.post(
            f"pathways/versions/{version}/validate",
            data=data,
            version=version
        )
        return response.get("data", {})

    async def get_trending_pathways(
        self,
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
            limit: Maximum number of results
            version: API version to use
            
        Returns:
            List of trending pathways
        """
        params = {"limit": limit}
        if industry_id:
            params["industry"] = industry_id
        if region:
            params["region"] = region
        if time_period:
            params["time_period"] = time_period

        response = await self.get(
            f"pathways/versions/{version}/trending",
            params=params,
            version=version
        )
        return response.get("data", [])

    async def get_pathways_metadata(
        self,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Career Pathways API metadata and version information.
        
        Args:
            version: API version to use
            
        Returns:
            API metadata and version information
        """
        response = await self.get(
            f"pathways/versions/{version}",
            version=version
        )
        return response.get("data", {})

    async def get_pathway_analysis(
        self,
        from_occupation_id: str,
        to_occupation_id: str,
        max_steps: int = 3,
        include_skill_analysis: bool = True,
        region: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get pathway analysis between two occupations (simplified endpoint).
        """
        params = {
            "from_occupation": from_occupation_id,
            "to_occupation": to_occupation_id,
            "max_steps": max_steps,
            "include_skills": include_skill_analysis
        }
        if region:
            params["region"] = region

        response = await self.get(
            f"versions/{version}/analyze",
            params=params,
            version=version
        )
        return response.get("data", {})
