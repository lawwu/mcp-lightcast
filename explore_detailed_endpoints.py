#!/usr/bin/env python3
"""Explore more specific endpoint patterns."""

import asyncio
import logging
from src.mcp_lightcast.apis.base import BaseLightcastClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def explore_working_endpoints():
    """Explore the working endpoints we found in more detail."""
    logger.info("🔍 Exploring Working Endpoints in Detail")
    
    discovered_endpoints = []
    
    try:
        async with BaseLightcastClient() as client:
            
            # Test Skills version metadata endpoint
            logger.info("\n📋 Skills Version Metadata:")
            try:
                response = await client.get("skills/versions/latest")
                logger.info(f"✅ Skills metadata: {list(response.get('data', {}).keys())}")
                discovered_endpoints.append({
                    "api": "skills",
                    "method": "GET", 
                    "path": "skills/versions/{version}",
                    "description": "Get skills version metadata and statistics",
                    "example": "skills/versions/latest"
                })
            except Exception as e:
                logger.error(f"❌ Skills metadata failed: {e}")
            
            # Test Skills search endpoint
            logger.info("\n📋 Skills Search:")
            try:
                response = await client.get("skills/versions/latest/skills", params={"q": "python", "limit": 3})
                logger.info(f"✅ Skills search: Found {len(response.get('data', []))} results")
                
                # Check what parameters are accepted
                params_to_test = [
                    {"q": "python", "limit": 2},
                    {"q": "python", "limit": 2, "type": "ST1"},
                    {"q": "python", "limit": 2, "category": "Information Technology"},
                    {"q": "python", "limit": 2, "subcategory": "Software Development"},
                    {"q": "python", "limit": 2, "isSoftware": "true"},
                    {"q": "python", "limit": 2, "isLanguage": "true"},
                ]
                
                for params in params_to_test:
                    try:
                        response = await client.get("skills/versions/latest/skills", params=params)
                        logger.info(f"   ✅ Params {params}: {len(response.get('data', []))} results")
                    except Exception as e:
                        logger.info(f"   ❌ Params {params}: {str(e)[:50]}")
                
                discovered_endpoints.append({
                    "api": "skills",
                    "method": "GET",
                    "path": "skills/versions/{version}/skills",
                    "description": "Search skills with various filters",
                    "example": "skills/versions/latest/skills?q=python&limit=10"
                })
            except Exception as e:
                logger.error(f"❌ Skills search failed: {e}")
            
            # Test Skills individual endpoint
            logger.info("\n📋 Skills Individual Resource:")
            try:
                # First get a skill ID
                search_response = await client.get("skills/versions/latest/skills", params={"q": "python", "limit": 1})
                if search_response.get("data"):
                    skill_id = search_response["data"][0]["id"]
                    skill_response = await client.get(f"skills/versions/latest/skills/{skill_id}")
                    logger.info(f"✅ Individual skill: {skill_response.get('data', {}).get('name', 'Unknown')}")
                    
                    discovered_endpoints.append({
                        "api": "skills",
                        "method": "GET",
                        "path": "skills/versions/{version}/skills/{id}",
                        "description": "Get detailed information about a specific skill",
                        "example": f"skills/versions/latest/skills/{skill_id}"
                    })
            except Exception as e:
                logger.error(f"❌ Individual skill failed: {e}")
            
            # Test Titles version metadata
            logger.info("\n📋 Titles Version Metadata:")
            try:
                response = await client.get("titles/versions/latest")
                logger.info(f"✅ Titles metadata: {list(response.get('data', {}).keys())}")
                discovered_endpoints.append({
                    "api": "titles",
                    "method": "GET",
                    "path": "titles/versions/{version}",
                    "description": "Get titles version metadata and statistics",
                    "example": "titles/versions/latest"
                })
            except Exception as e:
                logger.error(f"❌ Titles metadata failed: {e}")
            
            # Test Titles search endpoint
            logger.info("\n📋 Titles Search:")
            try:
                response = await client.get("titles/versions/latest/titles", params={"q": "engineer", "limit": 3})
                logger.info(f"✅ Titles search: Found {len(response.get('data', []))} results")
                
                # Test different parameters
                params_to_test = [
                    {"q": "engineer", "limit": 2},
                    {"q": "engineer", "limit": 2, "isSupervisor": "true"},
                    {"q": "engineer", "limit": 2, "levelBand": "Executive"},
                ]
                
                for params in params_to_test:
                    try:
                        response = await client.get("titles/versions/latest/titles", params=params)
                        logger.info(f"   ✅ Params {params}: {len(response.get('data', []))} results")
                    except Exception as e:
                        logger.info(f"   ❌ Params {params}: {str(e)[:50]}")
                
                discovered_endpoints.append({
                    "api": "titles",
                    "method": "GET",
                    "path": "titles/versions/{version}/titles",
                    "description": "Search titles with various filters",
                    "example": "titles/versions/latest/titles?q=engineer&limit=10"
                })
            except Exception as e:
                logger.error(f"❌ Titles search failed: {e}")
            
            # Test Titles individual endpoint
            logger.info("\n📋 Titles Individual Resource:")
            try:
                # First get a title ID
                search_response = await client.get("titles/versions/latest/titles", params={"q": "engineer", "limit": 1})
                if search_response.get("data"):
                    title_id = search_response["data"][0]["id"]
                    title_response = await client.get(f"titles/versions/latest/titles/{title_id}")
                    logger.info(f"✅ Individual title: {title_response.get('data', {}).get('name', 'Unknown')}")
                    
                    discovered_endpoints.append({
                        "api": "titles",
                        "method": "GET",
                        "path": "titles/versions/{version}/titles/{id}",
                        "description": "Get detailed information about a specific title",
                        "example": f"titles/versions/latest/titles/{title_id}"
                    })
            except Exception as e:
                logger.error(f"❌ Individual title failed: {e}")
            
            # Test Titles general metadata
            logger.info("\n📋 Titles General Metadata:")
            try:
                response = await client.get("titles/meta")
                logger.info(f"✅ Titles general metadata: {list(response.get('data', {}).keys())}")
                discovered_endpoints.append({
                    "api": "titles",
                    "method": "GET",
                    "path": "titles/meta",
                    "description": "Get general titles taxonomy metadata",
                    "example": "titles/meta"
                })
            except Exception as e:
                logger.error(f"❌ Titles general metadata failed: {e}")
                
    except Exception as e:
        logger.error(f"❌ Failed to explore endpoints: {e}")
    
    return discovered_endpoints

async def test_bulk_operations():
    """Test bulk operations that might be available."""
    logger.info("\n🔍 Testing Bulk Operations")
    
    bulk_endpoints = []
    
    try:
        async with BaseLightcastClient() as client:
            
            # Test bulk skills retrieval
            logger.info("\n📋 Testing Bulk Skills Retrieval:")
            
            # First get some skill IDs
            search_response = await client.get("skills/versions/latest/skills", params={"q": "python", "limit": 3})
            if search_response.get("data"):
                skill_ids = [skill["id"] for skill in search_response["data"]]
                logger.info(f"Got skill IDs for bulk testing: {skill_ids}")
                
                # Test POST with bulk IDs
                bulk_patterns = [
                    "skills/versions/latest/retrieve",
                    "skills/versions/latest/skills/retrieve", 
                    "skills/versions/latest/bulk",
                ]
                
                for pattern in bulk_patterns:
                    try:
                        response = await client.post(pattern, data={"ids": skill_ids})
                        logger.info(f"✅ POST {pattern} - Bulk retrieval works!")
                        bulk_endpoints.append({
                            "api": "skills",
                            "method": "POST",
                            "path": pattern,
                            "description": "Bulk retrieve multiple skills by IDs",
                            "example": f"POST {pattern} with ids: {skill_ids[:2]}"
                        })
                        break
                    except Exception as e:
                        if "404" not in str(e):
                            logger.info(f"   ⚠️  POST {pattern}: {str(e)[:50]}")
            
            # Test bulk titles retrieval  
            logger.info("\n📋 Testing Bulk Titles Retrieval:")
            
            # First get some title IDs
            search_response = await client.get("titles/versions/latest/titles", params={"q": "engineer", "limit": 3})
            if search_response.get("data"):
                title_ids = [title["id"] for title in search_response["data"]]
                logger.info(f"Got title IDs for bulk testing: {title_ids}")
                
                # Test POST with bulk IDs
                bulk_patterns = [
                    "titles/versions/latest/retrieve",
                    "titles/versions/latest/titles/retrieve",
                    "titles/versions/latest/bulk",
                ]
                
                for pattern in bulk_patterns:
                    try:
                        response = await client.post(pattern, data={"ids": title_ids})
                        logger.info(f"✅ POST {pattern} - Bulk retrieval works!")
                        bulk_endpoints.append({
                            "api": "titles",
                            "method": "POST", 
                            "path": pattern,
                            "description": "Bulk retrieve multiple titles by IDs",
                            "example": f"POST {pattern} with ids: {title_ids[:2]}"
                        })
                        break
                    except Exception as e:
                        if "404" not in str(e):
                            logger.info(f"   ⚠️  POST {pattern}: {str(e)[:50]}")
                            
    except Exception as e:
        logger.error(f"❌ Failed to test bulk operations: {e}")
    
    return bulk_endpoints

async def main():
    """Explore all endpoints in detail."""
    logger.info("🚀 Detailed Endpoint Exploration")
    logger.info("=" * 60)
    
    discovered = await explore_working_endpoints()
    bulk = await test_bulk_operations()
    
    all_endpoints = discovered + bulk
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 Complete API Endpoint Inventory")
    logger.info("=" * 60)
    
    skills_endpoints = [e for e in all_endpoints if e["api"] == "skills"]
    titles_endpoints = [e for e in all_endpoints if e["api"] == "titles"]
    
    logger.info(f"\n📋 Skills API Endpoints ({len(skills_endpoints)}):")
    for i, endpoint in enumerate(skills_endpoints, 1):
        logger.info(f"   {i}. {endpoint['method']} {endpoint['path']}")
        logger.info(f"      {endpoint['description']}")
        logger.info(f"      Example: {endpoint['example']}")
        logger.info("")
    
    logger.info(f"📋 Titles API Endpoints ({len(titles_endpoints)}):")
    for i, endpoint in enumerate(titles_endpoints, 1):
        logger.info(f"   {i}. {endpoint['method']} {endpoint['path']}")
        logger.info(f"      {endpoint['description']}")
        logger.info(f"      Example: {endpoint['example']}")
        logger.info("")
    
    logger.info(f"📈 Total Discovered Endpoints: {len(all_endpoints)}")
    
    return all_endpoints

if __name__ == "__main__":
    asyncio.run(main())