"""MCP tools for Lightcast Similarity API."""

from typing import Any

from fastmcp import FastMCP

from ..apis.similarity import SimilarityAPIClient


def register_similarity_tools(mcp: FastMCP):
    """Register all similarity-related MCP tools."""

    @mcp.tool
    async def find_similar_occupations(
        occupation_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Find occupations similar to a given occupation.
        
        Args:
            occupation_id: Lightcast occupation ID
            limit: Maximum number of similar occupations (default: 10)
            similarity_threshold: Minimum similarity score (default: 0.5)
            version: API version to use (default: "latest")
            
        Returns:
            List of similar occupations with similarity scores
        """
        async with SimilarityAPIClient() as client:
            results = await client.find_similar_occupations(occupation_id, limit, similarity_threshold, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "similarity_score": result.similarity_score,
                    "type": result.type
                }
                for result in results
            ]

    @mcp.tool
    async def find_similar_skills(
        skill_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Find skills similar to a given skill.
        
        Args:
            skill_id: Lightcast skill ID
            limit: Maximum number of similar skills (default: 10)
            similarity_threshold: Minimum similarity score (default: 0.5)
            version: API version to use (default: "latest")
            
        Returns:
            List of similar skills with similarity scores
        """
        async with SimilarityAPIClient() as client:
            results = await client.find_similar_skills(skill_id, limit, similarity_threshold, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "similarity_score": result.similarity_score,
                    "type": result.type
                }
                for result in results
            ]

    @mcp.tool
    async def get_occupation_skills(
        occupation_id: str,
        limit: int = 100,
        skill_type: str | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get skills associated with an occupation.
        
        Args:
            occupation_id: Lightcast occupation ID
            limit: Maximum number of skills (default: 100)
            skill_type: Filter by skill type (technical, soft, specialized)
            version: API version to use (default: "latest")
            
        Returns:
            Occupation skills mapping with details
        """
        async with SimilarityAPIClient() as client:
            result = await client.get_occupation_skills(occupation_id, limit, skill_type, version)
            return {
                "occupation_id": result.occupation_id,
                "occupation_name": result.occupation_name,
                "skills": result.skills,
                "total_skills": result.total_skills
            }

    @mcp.tool
    async def find_occupations_by_skills(
        skill_ids: list[str],
        limit: int = 10,
        match_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Find occupations that match a set of skills.
        
        Args:
            skill_ids: List of Lightcast skill IDs
            limit: Maximum number of occupations (default: 10)
            match_threshold: Minimum match score (default: 0.5)
            version: API version to use (default: "latest")
            
        Returns:
            List of matching occupations with match scores
        """
        async with SimilarityAPIClient() as client:
            results = await client.find_occupations_by_skills(skill_ids, limit, match_threshold, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "similarity_score": result.similarity_score,
                    "type": result.type
                }
                for result in results
            ]

    @mcp.tool
    async def calculate_skill_gaps(
        current_skills: list[str],
        target_occupation_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Calculate skill gaps between current skills and target occupation.
        
        Args:
            current_skills: List of current skill IDs
            target_occupation_id: Target occupation ID
            version: API version to use (default: "latest")
            
        Returns:
            Skill gap analysis
        """
        async with SimilarityAPIClient() as client:
            return await client.calculate_skill_gaps(current_skills, target_occupation_id, version)

    @mcp.tool
    async def compare_occupations(
        occupation_id_1: str,
        occupation_id_2: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Compare two occupations and their skill overlap.
        
        Args:
            occupation_id_1: First occupation ID
            occupation_id_2: Second occupation ID
            version: API version to use (default: "latest")
            
        Returns:
            Occupation comparison analysis
        """
        async with SimilarityAPIClient() as client:
            return await client.compare_occupations(occupation_id_1, occupation_id_2, version)

    @mcp.tool
    async def get_skill_transferability(
        from_occupation_id: str,
        to_occupation_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get skill transferability between two occupations.
        
        Args:
            from_occupation_id: Source occupation ID
            to_occupation_id: Target occupation ID
            version: API version to use (default: "latest")
            
        Returns:
            Skill transferability analysis
        """
        async with SimilarityAPIClient() as client:
            return await client.get_skill_transferability(from_occupation_id, to_occupation_id, version)

    @mcp.tool
    async def rank_occupations_by_similarity(
        target_occupation_id: str,
        candidate_occupation_ids: list[str],
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Rank a list of occupations by similarity to a target occupation.
        
        Args:
            target_occupation_id: Target occupation to compare against
            candidate_occupation_ids: List of occupation IDs to rank
            version: API version to use (default: "latest")
            
        Returns:
            List of occupations ranked by similarity
        """
        async with SimilarityAPIClient() as client:
            results = await client.rank_occupations_by_similarity(target_occupation_id, candidate_occupation_ids, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "similarity_score": result.similarity_score,
                    "type": result.type
                }
                for result in results
            ]

    @mcp.tool
    async def get_career_transitions(
        from_occupation_id: str,
        difficulty_level: str | None = None,
        industry_filter: list[str] | None = None,
        limit: int = 20,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Get potential career transitions from a given occupation.
        
        Args:
            from_occupation_id: Source occupation ID
            difficulty_level: Filter by transition difficulty (easy, medium, hard)
            industry_filter: Filter by target industries
            limit: Maximum number of results (default: 20)
            version: API version to use (default: "latest")
            
        Returns:
            List of potential career transitions
        """
        async with SimilarityAPIClient() as client:
            return await client.get_career_transitions(from_occupation_id, difficulty_level, industry_filter, limit, version)

    @mcp.tool
    async def find_skill_substitutes(
        skill_id: str,
        context_occupation_id: str | None = None,
        limit: int = 10,
        version: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        Find substitute skills that can replace a given skill.
        
        Args:
            skill_id: Target skill ID
            context_occupation_id: Occupation context for better substitution
            limit: Maximum number of results (default: 10)
            version: API version to use (default: "latest")
            
        Returns:
            List of substitute skills
        """
        async with SimilarityAPIClient() as client:
            results = await client.find_skill_substitutes(skill_id, context_occupation_id, limit, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "similarity_score": result.similarity_score,
                    "type": result.type
                }
                for result in results
            ]

    @mcp.tool
    async def get_similarity_metadata(
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Similarity API metadata and version information.
        
        Args:
            version: API version to use (default: "latest")
            
        Returns:
            API metadata and version information
        """
        async with SimilarityAPIClient() as client:
            return await client.get_similarity_metadata(version)
