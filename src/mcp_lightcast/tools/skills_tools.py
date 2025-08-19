"""MCP tools for Lightcast Skills API."""

from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

from src.mcp_lightcast.apis.skills import SkillsAPIClient


def register_skills_tools(mcp: FastMCP):
    """Register all skills-related MCP tools."""
    
    @mcp.tool
    async def search_skills(
        query: str,
        limit: int = 10,
        offset: int = 0,
        skill_type: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """
        Search for skills in the Lightcast skills database.
        
        Args:
            query: Search term for skills
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip (default: 0)
            skill_type: Filter by skill type (e.g., "Hard Skill", "Soft Skill")
            category: Filter by skill category
            subcategory: Filter by skill subcategory
            version: API version to use (default: "2023.4")
            
        Returns:
            List of matching skills with their details
        """
        async with SkillsAPIClient() as client:
            results = await client.search_skills(
                query, limit, offset, skill_type, category, subcategory, version
            )
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type,
                    "category": result.category,
                    "subcategory": result.subcategory
                }
                for result in results
            ]
    
    @mcp.tool
    async def get_skill_details(
        skill_id: str,
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific skill.
        
        Args:
            skill_id: Lightcast skill ID
            version: API version to use (default: "2023.4")
            
        Returns:
            Detailed skill information including description and metadata
        """
        async with SkillsAPIClient() as client:
            result = await client.get_skill_by_id(skill_id, version)
            return {
                "id": result.id,
                "name": result.name,
                "type": result.type,
                "category": result.category,
                "subcategory": result.subcategory,
                "description": result.description,
                "tags": result.tags,
                "info_url": result.infoUrl
            }
    
    @mcp.tool
    async def get_multiple_skills(
        skill_ids: List[str],
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """
        Get detailed information about multiple skills at once.
        
        Args:
            skill_ids: List of Lightcast skill IDs
            version: API version to use (default: "2023.4")
            
        Returns:
            List of detailed skill information for all requested skills
        """
        async with SkillsAPIClient() as client:
            results = await client.get_skills_by_ids(skill_ids, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type,
                    "category": result.category,
                    "subcategory": result.subcategory,
                    "description": result.description,
                    "tags": result.tags,
                    "info_url": result.infoUrl
                }
                for result in results
            ]
    
    @mcp.tool
    async def get_related_skills(
        skill_id: str,
        limit: int = 10,
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """
        Get skills related to a specific skill.
        
        Args:
            skill_id: Lightcast skill ID
            limit: Maximum number of related skills to return (default: 10)
            version: API version to use (default: "2023.4")
            
        Returns:
            List of related skills with similarity information
        """
        async with SkillsAPIClient() as client:
            results = await client.get_related_skills(skill_id, limit, version)
            return [
                {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type,
                    "category": result.category,
                    "subcategory": result.subcategory
                }
                for result in results
            ]
    
    @mcp.tool
    async def get_skill_categories(
        version: str = "2023.4"
    ) -> List[Dict[str, str]]:
        """
        Get all available skill categories and subcategories.
        
        Args:
            version: API version to use (default: "2023.4")
            
        Returns:
            List of skill categories and their subcategories
        """
        async with SkillsAPIClient() as client:
            return await client.get_skill_categories(version)
    
    @mcp.tool
    async def extract_skills_from_text(
        text: str,
        confidence_threshold: float = 0.5,
        version: str = "2023.4"
    ) -> List[Dict[str, Any]]:
        """
        Extract skills mentioned in a text description.
        
        Args:
            text: Text to analyze for skill mentions
            confidence_threshold: Minimum confidence score for skill extraction (default: 0.5)
            version: API version to use (default: "2023.4")
            
        Returns:
            List of extracted skills with confidence scores
        """
        async with SkillsAPIClient() as client:
            return await client.extract_skills_from_text(text, confidence_threshold, version)
    
    @mcp.tool
    async def get_skills_metadata(
        version: str = "2023.4"
    ) -> Dict[str, Any]:
        """
        Get metadata about the Lightcast skills taxonomy.
        
        Args:
            version: API version to use (default: "2023.4")
            
        Returns:
            Metadata about the skills database including statistics and version info
        """
        async with SkillsAPIClient() as client:
            return await client.get_skills_metadata(version)