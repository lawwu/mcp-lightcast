"""Lightcast Similarity API client."""

from typing import Any

from pydantic import BaseModel

from .base import BaseLightcastClient


class SimilarityResult(BaseModel):
    """Similarity result model."""
    id: str
    name: str
    similarity_score: float
    type: str | None = None


class OccupationSkillMapping(BaseModel):
    """Occupation to skills mapping result."""
    occupation_id: str
    occupation_name: str
    skills: list[dict[str, Any]]
    total_skills: int


class SimilarityAPIClient(BaseLightcastClient):
    """Client for Lightcast Similarity API."""

    def __init__(self):
        super().__init__(api_name="similarity")

    # Working endpoints discovered from testing
    async def get_available_models(self) -> list[str]:
        """
        Get list of available similarity models.
        
        Returns:
            List of available model names
        """
        response = await self.get("models")
        return response.get("data", [])

    async def get_api_metadata(self) -> dict[str, Any]:
        """
        Get comprehensive API metadata including model versions and taxonomy info.
        
        Returns:
            API metadata with models, versions, and supported taxonomies
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

    async def find_similar_occupations_soc(
        self,
        soc_code: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find occupations similar to a given SOC code.
        
        Args:
            soc_code: SOC occupation code (e.g., "15-1132.00")
            limit: Maximum number of results
            
        Returns:
            List of similar occupations with similarity scores
        """
        data = {
            "input": soc_code,
            "limit": limit
        }
        response = await self.post("models/soc", data=data)
        return response.get("data", [])

    async def find_similar_occupations_lotocc(
        self,
        lot_id: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find occupations similar to a given LOT occupation ID.
        
        Args:
            lot_id: LOT occupation ID (e.g., "7.39")
            limit: Maximum number of results
            
        Returns:
            List of similar occupations with similarity scores
        """
        data = {
            "input": lot_id,
            "limit": limit
        }
        response = await self.post("models/lotocc", data=data)
        return response.get("data", [])

    async def find_similar_occupations_onet(
        self,
        onet_code: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find occupations similar to a given O*NET code.
        
        Args:
            onet_code: O*NET occupation code
            limit: Maximum number of results
            
        Returns:
            List of similar occupations with similarity scores
        """
        data = {
            "input": onet_code,
            "limit": limit
        }
        response = await self.post("models/onet", data=data)
        return response.get("data", [])

    async def find_similar_skills_bulk(
        self,
        skill_ids: list[str],
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find skills similar to given skill IDs.
        
        Args:
            skill_ids: List of skill IDs
            limit: Maximum number of results
            
        Returns:
            List of similar skills with similarity scores
        """
        data = {
            "input": skill_ids,
            "limit": limit
        }
        response = await self.post("models/skill", data=data)
        return response.get("data", [])

    async def get_similar_occupations(
        self,
        occupation_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[SimilarityResult]:
        """Find occupations similar to a given occupation."""
        params = {
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }

        response = await self.get(
            f"versions/{version}/occupations/{occupation_id}/similar",
            params=params,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]

    async def get_similar_skills(
        self,
        skill_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[SimilarityResult]:
        """Find skills similar to a given skill."""
        params = {
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }

        response = await self.get(
            f"versions/{version}/skills/{skill_id}/similar",
            params=params,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]

    async def get_occupation_skills(
        self,
        occupation_id: str,
        limit: int = 100,
        skill_type: str | None = None,
        version: str = "latest"
    ) -> OccupationSkillMapping:
        """Get skills associated with an occupation."""
        params = {"limit": limit}
        if skill_type:
            params["skill_type"] = skill_type

        response = await self.get(
            f"versions/{version}/occupations/{occupation_id}/skills",
            params=params,
            version=version
        )

        data = response.get("data", {})
        return OccupationSkillMapping(
            occupation_id=occupation_id,
            occupation_name=data.get("occupation_name", ""),
            skills=data.get("skills", []),
            total_skills=data.get("total_skills", 0)
        )

    async def find_occupations_by_skills(
        self,
        skill_ids: list[str],
        limit: int = 10,
        match_threshold: float = 0.5,
        version: str = "latest"
    ) -> list[SimilarityResult]:
        """Find occupations that match a set of skills."""
        data = {
            "skill_ids": skill_ids,
            "limit": limit,
            "match_threshold": match_threshold
        }

        response = await self.post(
            f"similarity/versions/{version}/occupations/by_skills",
            data=data,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]

    async def calculate_skill_gaps(
        self,
        current_skills: list[str],
        target_occupation_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """Calculate skill gaps between current skills and target occupation."""
        data = {
            "current_skills": current_skills,
            "target_occupation_id": target_occupation_id
        }

        response = await self.post(
            f"similarity/versions/{version}/skill_gaps",
            data=data,
            version=version
        )
        return response.get("data", {})

    async def compare_occupations(
        self,
        occupation_id_1: str,
        occupation_id_2: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """Compare two occupations and their skill overlap."""
        params = {
            "occupation_1": occupation_id_1,
            "occupation_2": occupation_id_2
        }

        response = await self.get(
            f"similarity/versions/{version}/occupations/compare",
            params=params,
            version=version
        )
        return response.get("data", {})

    async def get_skill_transferability(
        self,
        from_occupation_id: str,
        to_occupation_id: str,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get skill transferability between two occupations.
        
        Args:
            from_occupation_id: Source occupation ID
            to_occupation_id: Target occupation ID
            version: API version to use
            
        Returns:
            Skill transferability analysis
        """
        params = {
            "from_occupation": from_occupation_id,
            "to_occupation": to_occupation_id
        }

        response = await self.get(
            f"similarity/versions/{version}/transferability",
            params=params,
            version=version
        )
        return response.get("data", {})

    async def rank_occupations_by_similarity(
        self,
        target_occupation_id: str,
        candidate_occupation_ids: list[str],
        version: str = "latest"
    ) -> list[SimilarityResult]:
        """
        Rank a list of occupations by similarity to a target occupation.
        
        Args:
            target_occupation_id: Target occupation to compare against
            candidate_occupation_ids: List of occupation IDs to rank
            version: API version to use
            
        Returns:
            List of occupations ranked by similarity
        """
        data = {
            "target_occupation": target_occupation_id,
            "candidates": candidate_occupation_ids
        }

        response = await self.post(
            f"similarity/versions/{version}/occupations/rank",
            data=data,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]

    async def get_career_transitions(
        self,
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
            limit: Maximum number of results
            version: API version to use
            
        Returns:
            List of potential career transitions
        """
        params = {"limit": limit}
        if difficulty_level:
            params["difficulty"] = difficulty_level
        if industry_filter:
            params["industries"] = ",".join(industry_filter)

        response = await self.get(
            f"similarity/versions/{version}/occupations/{from_occupation_id}/transitions",
            params=params,
            version=version
        )
        return response.get("data", [])

    async def analyze_skill_clusters(
        self,
        skill_ids: list[str],
        cluster_method: str = "hierarchical",
        num_clusters: int | None = None,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Analyze skill clustering and relationships.
        
        Args:
            skill_ids: List of skill IDs to cluster
            cluster_method: Clustering method (hierarchical, kmeans, dbscan)
            num_clusters: Number of clusters (for kmeans)
            version: API version to use
            
        Returns:
            Skill clustering analysis
        """
        data = {
            "skill_ids": skill_ids,
            "method": cluster_method
        }
        if num_clusters:
            data["num_clusters"] = num_clusters

        response = await self.post(
            f"similarity/versions/{version}/skills/cluster",
            data=data,
            version=version
        )
        return response.get("data", {})

    async def find_skill_substitutes(
        self,
        skill_id: str,
        context_occupation_id: str | None = None,
        limit: int = 10,
        version: str = "latest"
    ) -> list[SimilarityResult]:
        """
        Find substitute skills that can replace a given skill.
        
        Args:
            skill_id: Target skill ID
            context_occupation_id: Occupation context for better substitution
            limit: Maximum number of results
            version: API version to use
            
        Returns:
            List of substitute skills
        """
        params = {"limit": limit}
        if context_occupation_id:
            params["context_occupation"] = context_occupation_id

        response = await self.get(
            f"similarity/versions/{version}/skills/{skill_id}/substitutes",
            params=params,
            version=version
        )
        return [SimilarityResult(**item) for item in response.get("data", [])]

    async def get_occupation_similarity_matrix(
        self,
        occupation_ids: list[str],
        similarity_metric: str = "cosine",
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Generate similarity matrix for a set of occupations.
        
        Args:
            occupation_ids: List of occupation IDs
            similarity_metric: Similarity metric (cosine, jaccard, euclidean)
            version: API version to use
            
        Returns:
            Occupation similarity matrix
        """
        data = {
            "occupation_ids": occupation_ids,
            "metric": similarity_metric
        }

        response = await self.post(
            f"similarity/versions/{version}/occupations/matrix",
            data=data,
            version=version
        )
        return response.get("data", {})

    async def get_similarity_metadata(
        self,
        version: str = "latest"
    ) -> dict[str, Any]:
        """
        Get Similarity API metadata and version information.
        
        Args:
            version: API version to use
            
        Returns:
            API metadata and version information
        """
        response = await self.get(
            f"similarity/versions/{version}",
            version=version
        )
        return response.get("data", {})
