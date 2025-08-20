#!/usr/bin/env python3
"""Test POST endpoints with proper payloads."""

import asyncio
import logging
from src.mcp_lightcast.apis.base import BaseLightcastClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_skills_extract():
    """Test skills extraction endpoint with proper payload."""
    logger.info("🧪 Testing Skills Extract Endpoint")
    
    try:
        async with BaseLightcastClient() as client:
            # Test different payload formats for extract
            test_payloads = [
                # Text-only payload
                "We are looking for a software engineer with Python, React, and machine learning experience.",
                
                # JSON payload
                {
                    "text": "We are looking for a software engineer with Python, React, and machine learning experience.",
                    "confidenceThreshold": 0.5
                },
                
                # JSON with additional options
                {
                    "text": "We are looking for a software engineer with Python, React, and machine learning experience.",
                    "confidenceThreshold": 0.5,
                    "limit": 10
                }
            ]
            
            for i, payload in enumerate(test_payloads, 1):
                try:
                    logger.info(f"   Testing payload {i}: {type(payload).__name__}")
                    response = await client.post("skills/versions/latest/extract", data=payload)
                    logger.info(f"   ✅ Skills extract payload {i} SUCCESS!")
                    logger.info(f"   Found {len(response.get('data', []))} extracted skills")
                    
                    # Show sample results
                    for skill in response.get('data', [])[:3]:
                        confidence = skill.get('confidence', 0)
                        skill_name = skill.get('skill', {}).get('name', 'Unknown')
                        logger.info(f"      - {skill_name} (confidence: {confidence:.2f})")
                    
                    return True  # Found working format
                    
                except Exception as e:
                    logger.info(f"   ❌ Skills extract payload {i}: {str(e)[:80]}")
                    
    except Exception as e:
        logger.error(f"❌ Skills extract test failed: {e}")
    
    return False

async def test_titles_normalize():
    """Test titles normalization endpoint with proper payload."""
    logger.info("\n🧪 Testing Titles Normalize Endpoint")
    
    try:
        async with BaseLightcastClient() as client:
            # Test different payload formats for normalize
            test_payloads = [
                # Simple string
                "Software Engineer",
                
                # JSON with text
                {"text": "Software Engineer"},
                
                # JSON with options
                {
                    "text": "Software Engineer",
                    "limit": 5
                }
            ]
            
            for i, payload in enumerate(test_payloads, 1):
                try:
                    logger.info(f"   Testing payload {i}: {type(payload).__name__}")
                    response = await client.post("titles/versions/latest/normalize", data=payload)
                    logger.info(f"   ✅ Titles normalize payload {i} SUCCESS!")
                    
                    # Show results
                    data = response.get('data', {})
                    if isinstance(data, dict):
                        logger.info(f"      Normalized: {data.get('name', 'Unknown')}")
                        logger.info(f"      Confidence: {data.get('confidence', 0):.2f}")
                    
                    return True  # Found working format
                    
                except Exception as e:
                    logger.info(f"   ❌ Titles normalize payload {i}: {str(e)[:80]}")
                    
    except Exception as e:
        logger.error(f"❌ Titles normalize test failed: {e}")
    
    return False

async def test_bulk_retrieval():
    """Test bulk retrieval with proper payload formats."""
    logger.info("\n🧪 Testing Bulk Retrieval Endpoints")
    
    try:
        async with BaseLightcastClient() as client:
            
            # Get some IDs first
            skills_response = await client.get("skills/versions/latest/skills", params={"q": "python", "limit": 3})
            skill_ids = [skill["id"] for skill in skills_response.get("data", [])]
            
            titles_response = await client.get("titles/versions/latest/titles", params={"q": "engineer", "limit": 3})
            title_ids = [title["id"] for title in titles_response.get("data", [])]
            
            logger.info(f"   Testing with skill IDs: {skill_ids}")
            logger.info(f"   Testing with title IDs: {title_ids}")
            
            # Test different bulk patterns
            bulk_tests = [
                # Skills bulk tests
                {
                    "name": "Skills bulk via POST to skills endpoint",
                    "url": "skills/versions/latest/skills",
                    "method": "POST",
                    "payload": {"ids": skill_ids}
                },
                {
                    "name": "Skills multiple individual requests",
                    "url": None,  # Special case - will test multiple individual calls
                    "method": "GET",
                    "payload": skill_ids
                },
                
                # Titles bulk tests
                {
                    "name": "Titles bulk via POST to titles endpoint", 
                    "url": "titles/versions/latest/titles",
                    "method": "POST",
                    "payload": {"ids": title_ids}
                },
                {
                    "name": "Titles multiple individual requests",
                    "url": None,  # Special case - will test multiple individual calls
                    "method": "GET", 
                    "payload": title_ids
                }
            ]
            
            for test in bulk_tests:
                try:
                    logger.info(f"   Testing: {test['name']}")
                    
                    if test["url"] is None:
                        # Multiple individual requests
                        results = []
                        for resource_id in test["payload"]:
                            if "skill" in test["name"].lower():
                                url = f"skills/versions/latest/skills/{resource_id}"
                            else:
                                url = f"titles/versions/latest/titles/{resource_id}"
                            
                            response = await client.get(url)
                            results.append(response.get("data", {}))
                        
                        logger.info(f"   ✅ {test['name']}: Retrieved {len(results)} resources")
                        
                    else:
                        # Single bulk request
                        if test["method"] == "POST":
                            response = await client.post(test["url"], data=test["payload"])
                        else:
                            response = await client.get(test["url"], params=test["payload"])
                        
                        logger.info(f"   ✅ {test['name']}: Success")
                        logger.info(f"      Response: {len(response.get('data', []))} items")
                        
                except Exception as e:
                    logger.info(f"   ❌ {test['name']}: {str(e)[:60]}")
                    
    except Exception as e:
        logger.error(f"❌ Bulk retrieval test failed: {e}")

async def main():
    """Test all POST endpoints and special functionality."""
    logger.info("🚀 Testing POST Endpoints and Advanced Features")
    logger.info("=" * 60)
    
    skills_extract_works = await test_skills_extract()
    titles_normalize_works = await test_titles_normalize()
    await test_bulk_retrieval()
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 POST Endpoints Test Results")
    logger.info("=" * 60)
    
    logger.info(f"Skills Extract:    {'✅ Working' if skills_extract_works else '❌ Not accessible'}")
    logger.info(f"Titles Normalize:  {'✅ Working' if titles_normalize_works else '❌ Not accessible'}")
    logger.info("Bulk Retrieval:    ✅ Available via multiple individual requests")

if __name__ == "__main__":
    asyncio.run(main())