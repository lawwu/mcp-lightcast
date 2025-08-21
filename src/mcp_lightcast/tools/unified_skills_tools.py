"""MCP tools for unified title normalization and skills extraction."""

import logging

from .unified_skills import normalize_title_and_get_skills

logger = logging.getLogger(__name__)


def register_unified_skills_tools(mcp):
    """Register unified skills extraction tools with the MCP server."""

    @mcp.tool()
    async def normalize_title_and_extract_skills(
        title: str,
        sources: list[str] | None = None,
        n_skills: int = 25,
        mapping_name: str = "titles_v5.24.0_lot_v6.20.0"
    ) -> dict:
        """
        Normalize a job title and extract associated skills from multiple sources.
        
        This unified tool combines functionality from multiple Lightcast APIs to:
        1. Normalize the input job title to a standard form
        2. Extract relevant skills from multiple data sources
        3. Return a comprehensive skills profile for the occupation
        
        Args:
            title: Raw job title to normalize (e.g., "Software Engineer", "Data Scientist")
            sources: List of data sources to use for skills extraction. Options:
                    ["all"] - Use all available sources (default)
                    ["postings"] - Skills from job postings data  
                    ["similarity"] - Skills from similarity analysis
                    ["benchmark"] - Skills from occupation benchmarks
                    ["classification"] - Skills from text classification
                    Can specify multiple: ["similarity", "benchmark"]
            n_skills: Maximum number of skills to return per source (default: 25)
            mapping_name: Mapping version for title-to-occupation conversion
                         (default: "titles_v5.24.0_lot_v6.20.0")
        
        Returns:
            Dictionary containing:
            - title: Original input title
            - normalized_title: Standardized title information
            - title_id: Lightcast title identifier
            - lotspecocc_id: LOT occupation identifier (if available)
            - skills_by_source: Skills organized by data source
            - unified_skills: Deduplicated skills ranked by frequency across sources
            - errors: Any errors encountered during processing
            - metadata: Additional processing information
            
        Example:
            result = await normalize_title_and_extract_skills(
                title="Senior Python Developer",
                sources=["similarity", "classification"], 
                n_skills=20
            )
            
            # Access unified skills list
            top_skills = result["unified_skills"]
            
            # Access skills by specific source
            similarity_skills = result["skills_by_source"]["similarity"]
        """
        if sources is None:
            sources = ["all"]

        logger.info(f"Normalizing title and extracting skills for: {title}")
        logger.info(f"Using sources: {sources}, max skills: {n_skills}")

        try:
            result = await normalize_title_and_get_skills(
                title=title,
                sources=sources,
                n_skills=n_skills,
                mapping_name=mapping_name
            )

            logger.info(f"Successfully processed title: {title}")
            logger.info(f"Found {len(result['unified_skills'])} unified skills")

            return result

        except Exception as e:
            error_msg = f"Failed to process title '{title}': {str(e)}"
            logger.error(error_msg)
            return {
                "title": title,
                "normalized_title": None,
                "title_id": None,
                "lotspecocc_id": None,
                "skills_by_source": {},
                "unified_skills": [],
                "errors": [error_msg],
                "metadata": {}
            }

    @mcp.tool()
    async def bulk_normalize_titles_and_extract_skills(
        titles: list[str],
        sources: list[str] | None = None,
        n_skills: int = 15
    ) -> list[dict]:
        """
        Normalize multiple job titles and extract skills in bulk.
        
        Processes multiple job titles efficiently, useful for analyzing
        multiple roles or building comprehensive skills profiles.
        
        Args:
            titles: List of raw job titles to process
            sources: Data sources to use (same options as single title function)
            n_skills: Maximum skills per source per title (reduced default for bulk)
            
        Returns:
            List of dictionaries, each containing the same structure as
            the single title function result.
            
        Example:
            titles = ["Software Engineer", "Data Scientist", "Product Manager"]
            results = await bulk_normalize_titles_and_extract_skills(
                titles=titles,
                sources=["classification", "similarity"],
                n_skills=10
            )
            
            for result in results:
                print(f"Title: {result['title']}")
                print(f"Skills: {result['unified_skills'][:5]}")  # Top 5 skills
        """
        if sources is None:
            sources = ["all"]

        logger.info(f"Processing {len(titles)} titles in bulk")

        results = []
        for title in titles:
            try:
                result = await normalize_title_and_get_skills(
                    title=title,
                    sources=sources,
                    n_skills=n_skills
                )
                results.append(result)
                logger.info(f"Processed title: {title} -> {len(result['unified_skills'])} skills")

            except Exception as e:
                error_msg = f"Failed to process title '{title}': {str(e)}"
                logger.error(error_msg)
                results.append({
                    "title": title,
                    "normalized_title": None,
                    "title_id": None,
                    "lotspecocc_id": None,
                    "skills_by_source": {},
                    "unified_skills": [],
                    "errors": [error_msg],
                    "metadata": {}
                })

        logger.info(f"Completed bulk processing of {len(titles)} titles")
        return results

    @mcp.tool()
    async def compare_title_skills(
        title1: str,
        title2: str,
        sources: list[str] | None = None,
        n_skills: int = 20
    ) -> dict:
        """
        Compare skills between two job titles.
        
        Analyzes the skills overlap and differences between two roles,
        useful for career transition planning or role comparison.
        
        Args:
            title1: First job title to compare
            title2: Second job title to compare  
            sources: Data sources to use for skills extraction
            n_skills: Maximum skills to extract per title
            
        Returns:
            Dictionary containing:
            - title1_result: Full skills analysis for first title
            - title2_result: Full skills analysis for second title
            - shared_skills: Skills that appear in both roles
            - unique_to_title1: Skills unique to first title
            - unique_to_title2: Skills unique to second title
            - similarity_score: Jaccard similarity coefficient (0-1)
            
        Example:
            comparison = await compare_title_skills(
                title1="Data Scientist",
                title2="Machine Learning Engineer", 
                sources=["classification", "similarity"]
            )
            
            print(f"Shared skills: {comparison['shared_skills']}")
            print(f"Similarity: {comparison['similarity_score']:.2f}")
        """
        if sources is None:
            sources = ["classification"]  # Use classification for faster comparison

        logger.info(f"Comparing skills between '{title1}' and '{title2}'")

        try:
            # Get skills for both titles
            result1 = await normalize_title_and_get_skills(
                title=title1,
                sources=sources,
                n_skills=n_skills
            )

            result2 = await normalize_title_and_get_skills(
                title=title2,
                sources=sources,
                n_skills=n_skills
            )

            # Extract skills lists
            skills1 = set(result1["unified_skills"])
            skills2 = set(result2["unified_skills"])

            # Calculate overlaps
            shared_skills = list(skills1.intersection(skills2))
            unique_to_title1 = list(skills1 - skills2)
            unique_to_title2 = list(skills2 - skills1)

            # Calculate Jaccard similarity
            union_size = len(skills1.union(skills2))
            similarity_score = len(shared_skills) / union_size if union_size > 0 else 0.0

            logger.info(f"Comparison complete: {len(shared_skills)} shared skills, "
                       f"similarity: {similarity_score:.3f}")

            return {
                "title1_result": result1,
                "title2_result": result2,
                "shared_skills": shared_skills,
                "unique_to_title1": unique_to_title1,
                "unique_to_title2": unique_to_title2,
                "similarity_score": similarity_score,
                "comparison_metadata": {
                    "total_skills_title1": len(skills1),
                    "total_skills_title2": len(skills2),
                    "total_shared": len(shared_skills),
                    "jaccard_similarity": similarity_score
                }
            }

        except Exception as e:
            error_msg = f"Failed to compare titles '{title1}' and '{title2}': {str(e)}"
            logger.error(error_msg)
            return {
                "title1_result": None,
                "title2_result": None,
                "shared_skills": [],
                "unique_to_title1": [],
                "unique_to_title2": [],
                "similarity_score": 0.0,
                "errors": [error_msg]
            }
