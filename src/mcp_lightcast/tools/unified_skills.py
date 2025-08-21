"""Unified title normalization and skills extraction tool."""

import logging
from enum import Enum
from typing import Any

from ..apis.classification import ClassificationAPIClient
from ..apis.occupation_benchmark import OccupationBenchmarkAPIClient
from ..apis.similarity import SimilarityAPIClient
from ..apis.skills import SkillsAPIClient
from ..apis.titles import TitlesAPIClient


class SkillsSource(str, Enum):
    """Available sources for skills extraction."""
    POSTINGS = "postings"
    SIMILARITY = "similarity"
    BENCHMARK = "benchmark"
    CLASSIFICATION = "classification"
    ALL = "all"


class UnifiedSkillsResult:
    """Result container for unified skills extraction."""

    def __init__(self):
        self.title: str | None = None
        self.normalized_title: dict[str, Any] | None = None
        self.title_id: str | None = None
        self.lotspecocc_id: str | None = None
        self.skills_by_source: dict[str, list[str]] = {}
        self.errors: list[str] = []
        self.metadata: dict[str, Any] = {}

    def get_unified_skills(self, max_skills: int = 25) -> list[str]:
        """Get unified skills list from all sources, removing duplicates."""
        all_skills = []
        skill_counts = {}

        # Count occurrences of each skill across sources
        for source, skills in self.skills_by_source.items():
            for skill in skills:
                if skill not in skill_counts:
                    skill_counts[skill] = 0
                skill_counts[skill] += 1

        # Sort by frequency (skills appearing in multiple sources first)
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)

        # Return unique skills up to max_skills limit
        return [skill for skill, count in sorted_skills[:max_skills]]


class UnifiedSkillsExtractor:
    """Unified tool that normalizes titles and extracts skills from multiple sources."""

    def __init__(self):
        self.titles_client = TitlesAPIClient()
        self.skills_client = SkillsAPIClient()
        self.similarity_client = SimilarityAPIClient()
        self.benchmark_client = OccupationBenchmarkAPIClient()
        self.classification_client = ClassificationAPIClient()
        self.logger = logging.getLogger(__name__)

    async def normalize_title_and_get_skills(
        self,
        title: str,
        sources: list[SkillsSource] = [SkillsSource.ALL],
        n_skills: int = 25,
        mapping_name: str = "titles_v5.47.0_lot_v7.7.0"
    ) -> UnifiedSkillsResult:
        """
        Normalize a title and extract skills from multiple sources.
        
        Args:
            title: Raw job title to normalize
            sources: List of sources to use for skills extraction
            n_skills: Maximum number of skills to return per source
            mapping_name: Mapping name for title to LOT occupation mapping
            
        Returns:
            UnifiedSkillsResult with skills from all requested sources
        """
        result = UnifiedSkillsResult()
        result.title = title

        # Expand 'all' source to include all available sources
        if SkillsSource.ALL in sources:
            sources = [SkillsSource.POSTINGS, SkillsSource.SIMILARITY,
                      SkillsSource.BENCHMARK, SkillsSource.CLASSIFICATION]

        try:
            # Step 1: Normalize the title (ensure correct scope)
            self.logger.info(f"Normalizing title: {title}")

            # Set the correct scope for titles API
            from ..auth.oauth import lightcast_auth
            lightcast_auth._scope = "emsi_open"
            lightcast_auth._token = None  # Force token refresh with new scope

            normalized_result = await self.titles_client.normalize_title(title)

            if not normalized_result or "data" not in normalized_result:
                raise ValueError("Title normalization failed")

            result.normalized_title = normalized_result["data"]
            result.title_id = normalized_result["data"]["title"]["id"]
            result.metadata["normalized_title_data"] = normalized_result

            # Step 2: Get LOT Specialized Occupation ID if needed
            if any(source in [SkillsSource.SIMILARITY, SkillsSource.BENCHMARK] for source in sources):
                try:
                    result.lotspecocc_id = await self._map_title_id_to_lotspecocc_id(
                        result.title_id, mapping_name
                    )
                    result.metadata["lotspecocc_id"] = result.lotspecocc_id
                except Exception as e:
                    error_msg = f"Failed to get LOT occupation ID: {str(e)}"
                    self.logger.error(error_msg)
                    result.errors.append(error_msg)

            # Step 3: Extract skills from each requested source
            for source in sources:
                try:
                    if source == SkillsSource.POSTINGS:
                        skills = await self._get_skills_from_postings(result.title_id, n_skills)
                        result.skills_by_source["postings"] = skills

                    elif source == SkillsSource.SIMILARITY:
                        if result.lotspecocc_id:
                            # Set the correct scope for similarity API
                            lightcast_auth._scope = "similarity"
                            lightcast_auth._token = None  # Force token refresh with new scope

                            skills = await self._get_skills_from_similarity(result.lotspecocc_id, n_skills)
                            result.skills_by_source["similarity"] = skills
                        else:
                            result.errors.append("Cannot get similarity skills: LOT occupation ID not available")

                    elif source == SkillsSource.BENCHMARK:
                        if result.lotspecocc_id:
                            # Set the correct scope for benchmark API
                            lightcast_auth._scope = "occupation-benchmark"
                            lightcast_auth._token = None  # Force token refresh with new scope

                            skills = await self._get_skills_from_benchmark(result.lotspecocc_id, n_skills)
                            result.skills_by_source["benchmark"] = skills
                        else:
                            result.errors.append("Cannot get benchmark skills: LOT occupation ID not available")

                    elif source == SkillsSource.CLASSIFICATION:
                        # Set the correct scope for classification API
                        lightcast_auth._scope = "classification_api"
                        lightcast_auth._token = None  # Force token refresh with new scope

                        skills = await self._get_skills_from_classification(title, n_skills)
                        result.skills_by_source["classification"] = skills

                except Exception as e:
                    error_msg = f"Failed to get skills from {source}: {str(e)}"
                    self.logger.error(error_msg)
                    result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Title normalization failed: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)

        return result

    async def _map_title_id_to_lotspecocc_id(
        self,
        title_id: str,
        mapping_name: str = "titles_v5.47.0_lot_v7.7.0"
    ) -> str:
        """Map title ID to LOT Specialized Occupation ID."""
        # Set the correct scope for classification API (mapping uses classification scope)
        from ..auth.oauth import lightcast_auth
        lightcast_auth._scope = "classification_api"
        lightcast_auth._token = None  # Force token refresh with new scope

        self.logger.info(f"Mapping title ID {title_id} to LOT occupation using {mapping_name}")

        try:
            lotspecocc_id = await self.classification_client.map_title_id_to_lotspecocc_id(
                title_id=title_id,
                mapping_name=mapping_name
            )
            self.logger.info(f"Mapped title ID {title_id} to LOT occupation {lotspecocc_id}")
            return lotspecocc_id
        except KeyError as e:
            self.logger.error(f"Mapping failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected mapping error: {e}")
            raise

    async def _get_skills_from_postings(self, title_id: str, n_skills: int) -> list[str]:
        """Get skills from postings data (simulated - needs actual postings API)."""
        # This would use the postings API to get skills for a title ID
        # Since the postings API wasn't fully implemented in our current scope,
        # we'll use the Skills API as a fallback
        self.logger.warning("Postings API not available, using Skills API search as fallback")

        # Use skills search as a reasonable fallback
        skills_results = await self.skills_client.search_skills(
            query=f"title_id:{title_id}",
            limit=n_skills
        )

        skills = []
        if skills_results and "data" in skills_results:
            skills = [skill.get("name", "") for skill in skills_results["data"][:n_skills] if skill.get("name")]

        return skills

    async def _get_skills_from_similarity(self, lotspecocc_id: str, n_skills: int) -> list[str]:
        """Get skills using the Similarity API."""
        # Use the similarity API with lotspecocc-skill model to find skills related to the LOT occupation
        data = {
            "input": lotspecocc_id,
            "limit": n_skills
        }
        similarity_results = await self.similarity_client.post("models/lotspecocc-skill", data=data)

        skills = []
        if similarity_results and "data" in similarity_results:
            skills = [skill.get("name", "") for skill in similarity_results["data"][:n_skills] if skill.get("name")]

        return skills

    async def _get_skills_from_benchmark(self, lotspecocc_id: str, n_skills: int) -> list[str]:
        """Get skills using the Occupation Benchmark API."""
        try:
            # Try to get benchmark data for the occupation
            benchmark_data = await self.benchmark_client.get_occupation_benchmark(
                occupation_id=lotspecocc_id,
                metrics=["skills", "certifications"]  # Request skills-related metrics
            )

            skills = []
            if benchmark_data and hasattr(benchmark_data, 'metrics'):
                # Extract skill names from benchmark metrics
                for metric in benchmark_data.metrics:
                    if "skill" in metric.metric_name.lower():
                        skills.append(metric.metric_name)

            return skills[:n_skills]

        except Exception as e:
            # Fallback: Use the working dimension endpoint to get general info
            self.logger.warning(f"Primary benchmark approach failed: {e}")
            try:
                dimension_data = await self.benchmark_client.get_lotspecocc_dimension()
                # This won't give us skills, but at least we can confirm the API is working
                self.logger.info("Benchmark API working, but no specific skills data available")
                return []  # Return empty list since we can't extract specific skills
            except Exception as fallback_e:
                self.logger.error(f"Benchmark fallback also failed: {fallback_e}")
                return []

    async def _get_skills_from_classification(self, title: str, n_skills: int) -> list[str]:
        """Get skills using the Classification API."""
        # Extract skills directly from the job title text
        classification_result = await self.classification_client.extract_skills_from_text(
            text=title,
            confidence_threshold=0.5
        )

        skills = []
        if classification_result and classification_result.concepts:
            skills = [
                concept.concept.get("name", "")
                for concept in classification_result.concepts[:n_skills]
                if concept.concept.get("name")
            ]

        return skills


# Main unified function for easy access
async def normalize_title_and_get_skills(
    title: str,
    sources: list[str] = ["all"],
    n_skills: int = 25,
    mapping_name: str = "titles_v5.47.0_lot_v7.7.0"
) -> dict[str, Any]:
    """
    Unified function to normalize a title and get skills from multiple sources.
    
    Args:
        title: Raw job title to normalize
        sources: List of sources ("postings", "similarity", "benchmark", "classification", "all")
        n_skills: Maximum number of skills to return per source
        mapping_name: Mapping name for title to LOT occupation mapping
        
    Returns:
        Dictionary with normalized title info and skills from all sources
    """
    # Convert string sources to enum
    source_enums = []
    for source in sources:
        if source.lower() == "all":
            source_enums.append(SkillsSource.ALL)
        elif source.lower() == "postings":
            source_enums.append(SkillsSource.POSTINGS)
        elif source.lower() == "similarity":
            source_enums.append(SkillsSource.SIMILARITY)
        elif source.lower() == "benchmark":
            source_enums.append(SkillsSource.BENCHMARK)
        elif source.lower() == "classification":
            source_enums.append(SkillsSource.CLASSIFICATION)

    extractor = UnifiedSkillsExtractor()
    result = await extractor.normalize_title_and_get_skills(
        title=title,
        sources=source_enums,
        n_skills=n_skills,
        mapping_name=mapping_name
    )

    # Convert to dictionary for JSON serialization
    return {
        "title": result.title,
        "normalized_title": result.normalized_title,
        "title_id": result.title_id,
        "lotspecocc_id": result.lotspecocc_id,
        "skills_by_source": result.skills_by_source,
        "unified_skills": result.get_unified_skills(n_skills),
        "errors": result.errors,
        "metadata": result.metadata
    }
