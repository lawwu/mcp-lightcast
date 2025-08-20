#!/usr/bin/env python3
"""Systematically discover all available endpoints in Skills and Titles APIs."""

import asyncio
import logging
from src.mcp_lightcast.apis.base import BaseLightcastClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def discover_skills_endpoints():
    """Discover all Skills API endpoints."""
    logger.info("🔍 Discovering Skills API Endpoints")
    
    base_patterns = [
        "skills/versions/latest",
        "skills/versions/latest/skills",
        "skills/versions/latest/extract",
        "skills/versions/latest/normalize", 
        "skills/versions/latest/categories",
        "skills/versions/latest/subcategories",
        "skills/versions/latest/types",
        "skills/versions/latest/meta",
        "skills/versions/latest/retrieve",
        "skills/versions/latest/related",
        "skills/versions/latest/search",
        "skills/versions/latest/compare",
        "skills/versions/latest/suggest",
        "skills/versions/latest/similar",
        "skills/extract",
        "skills/normalize",
        "skills/categories",
        "skills/types"
    ]
    
    skills_endpoints = []
    
    try:
        async with BaseLightcastClient() as client:
            for pattern in base_patterns:
                try:
                    # Test GET request
                    response = await client.get(pattern, params={"limit": 1})
                    logger.info(f"✅ GET {pattern} - SUCCESS")
                    skills_endpoints.append(("GET", pattern, "Working"))
                except Exception as e:
                    if "404" not in str(e):
                        logger.info(f"⚠️  GET {pattern} - {str(e)[:60]}")
                        skills_endpoints.append(("GET", pattern, str(e)[:60]))
                    
                # Test POST request for some endpoints
                if any(word in pattern for word in ["extract", "normalize", "retrieve"]):
                    try:
                        response = await client.post(pattern, data={"test": "data"})
                        logger.info(f"✅ POST {pattern} - SUCCESS")
                        skills_endpoints.append(("POST", pattern, "Working"))
                    except Exception as e:
                        if "404" not in str(e) and "400" not in str(e):
                            logger.info(f"⚠️  POST {pattern} - {str(e)[:60]}")
                            skills_endpoints.append(("POST", pattern, str(e)[:60]))
                            
    except Exception as e:
        logger.error(f"❌ Failed to test Skills endpoints: {e}")
    
    return skills_endpoints

async def discover_titles_endpoints():
    """Discover all Titles API endpoints."""
    logger.info("\n🔍 Discovering Titles API Endpoints")
    
    base_patterns = [
        "titles/versions/latest",
        "titles/versions/latest/titles",
        "titles/versions/latest/normalize",
        "titles/versions/latest/search",
        "titles/versions/latest/meta",
        "titles/versions/latest/hierarchy",
        "titles/versions/latest/related",
        "titles/versions/latest/suggest",
        "titles/versions/latest/compare",
        "titles/versions/latest/similar",
        "titles/normalize",
        "titles/search",
        "titles/meta"
    ]
    
    titles_endpoints = []
    
    try:
        async with BaseLightcastClient() as client:
            for pattern in base_patterns:
                try:
                    # Test GET request
                    response = await client.get(pattern, params={"limit": 1})
                    logger.info(f"✅ GET {pattern} - SUCCESS")
                    titles_endpoints.append(("GET", pattern, "Working"))
                except Exception as e:
                    if "404" not in str(e):
                        logger.info(f"⚠️  GET {pattern} - {str(e)[:60]}")
                        titles_endpoints.append(("GET", pattern, str(e)[:60]))
                
                # Test POST request for some endpoints
                if any(word in pattern for word in ["normalize", "search"]):
                    try:
                        response = await client.post(pattern, data="test title")
                        logger.info(f"✅ POST {pattern} - SUCCESS") 
                        titles_endpoints.append(("POST", pattern, "Working"))
                    except Exception as e:
                        if "404" not in str(e) and "400" not in str(e):
                            logger.info(f"⚠️  POST {pattern} - {str(e)[:60]}")
                            titles_endpoints.append(("POST", pattern, str(e)[:60]))
                            
    except Exception as e:
        logger.error(f"❌ Failed to test Titles endpoints: {e}")
    
    return titles_endpoints

async def test_individual_resource_endpoints():
    """Test endpoints that require individual resource IDs."""
    logger.info("\n🔍 Testing Individual Resource Endpoints")
    
    # First get some IDs to test with
    test_endpoints = []
    
    try:
        async with BaseLightcastClient() as client:
            # Get a skill ID
            skills_response = await client.get("skills/versions/latest/skills", params={"q": "python", "limit": 1})
            if skills_response.get("data"):
                skill_id = skills_response["data"][0]["id"]
                logger.info(f"Found skill ID for testing: {skill_id}")
                
                # Test skill-specific endpoints
                skill_patterns = [
                    f"skills/versions/latest/skills/{skill_id}",
                    f"skills/versions/latest/skills/{skill_id}/related",
                    f"skills/versions/latest/{skill_id}",
                ]
                
                for pattern in skill_patterns:
                    try:
                        response = await client.get(pattern)
                        logger.info(f"✅ GET {pattern} - SUCCESS")
                        test_endpoints.append(("GET", pattern, "Working"))
                    except Exception as e:
                        if "404" not in str(e):
                            logger.info(f"⚠️  GET {pattern} - {str(e)[:60]}")
                            test_endpoints.append(("GET", pattern, str(e)[:60]))
            
            # Get a title ID
            titles_response = await client.get("titles/versions/latest/titles", params={"q": "engineer", "limit": 1})
            if titles_response.get("data"):
                title_id = titles_response["data"][0]["id"]
                logger.info(f"Found title ID for testing: {title_id}")
                
                # Test title-specific endpoints
                title_patterns = [
                    f"titles/versions/latest/titles/{title_id}",
                    f"titles/versions/latest/titles/{title_id}/related",
                    f"titles/versions/latest/titles/{title_id}/hierarchy",
                    f"titles/versions/latest/{title_id}",
                ]
                
                for pattern in title_patterns:
                    try:
                        response = await client.get(pattern)
                        logger.info(f"✅ GET {pattern} - SUCCESS")
                        test_endpoints.append(("GET", pattern, "Working"))
                    except Exception as e:
                        if "404" not in str(e):
                            logger.info(f"⚠️  GET {pattern} - {str(e)[:60]}")
                            test_endpoints.append(("GET", pattern, str(e)[:60]))
                            
    except Exception as e:
        logger.error(f"❌ Failed to test individual resource endpoints: {e}")
    
    return test_endpoints

async def main():
    """Discover all endpoints and create implementation plan."""
    logger.info("🚀 Comprehensive API Endpoint Discovery")
    logger.info("=" * 60)
    
    skills_endpoints = await discover_skills_endpoints()
    titles_endpoints = await discover_titles_endpoints()
    individual_endpoints = await test_individual_resource_endpoints()
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 Discovery Results Summary")
    logger.info("=" * 60)
    
    logger.info(f"\n📋 Skills API Endpoints Found:")
    working_skills = [e for e in skills_endpoints if "Working" in e[2]]
    for method, path, status in working_skills:
        logger.info(f"   {method:4} {path}")
    
    logger.info(f"\n📋 Titles API Endpoints Found:")
    working_titles = [e for e in titles_endpoints if "Working" in e[2]]
    for method, path, status in working_titles:
        logger.info(f"   {method:4} {path}")
    
    logger.info(f"\n📋 Individual Resource Endpoints Found:")
    working_individual = [e for e in individual_endpoints if "Working" in e[2]]
    for method, path, status in working_individual:
        logger.info(f"   {method:4} {path}")
    
    logger.info(f"\n📈 Summary:")
    logger.info(f"   Skills endpoints: {len(working_skills)}")
    logger.info(f"   Titles endpoints: {len(working_titles)}")
    logger.info(f"   Individual endpoints: {len(working_individual)}")
    logger.info(f"   Total working endpoints: {len(working_skills) + len(working_titles) + len(working_individual)}")

if __name__ == "__main__":
    asyncio.run(main())