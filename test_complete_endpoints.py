#!/usr/bin/env python3
"""Comprehensive testing of all implemented Lightcast API endpoints."""

import asyncio
import logging
import json
from typing import List, Dict, Any
from src.mcp_lightcast.apis.skills import SkillsAPIClient
from src.mcp_lightcast.apis.titles import TitlesAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EndpointTester:
    """Test runner for all API endpoints."""
    
    def __init__(self):
        self.test_results = {
            "skills": {},
            "titles": {}
        }
    
    async def test_skills_endpoints(self):
        """Test all Skills API endpoints."""
        logger.info("🧪 Testing Skills API Endpoints")
        logger.info("=" * 50)
        
        async with SkillsAPIClient() as client:
            # Test 1: Search Skills
            try:
                results = await client.search_skills("python", limit=5)
                self.test_results["skills"]["search_skills"] = {
                    "status": "✅ PASS",
                    "count": len(results),
                    "sample": results[0].name if results else None
                }
                logger.info(f"✅ search_skills: Found {len(results)} skills")
                if results:
                    logger.info(f"   Sample: {results[0].name}")
            except Exception as e:
                self.test_results["skills"]["search_skills"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ search_skills: {e}")
            
            # Test 2: Get Skill by ID (using first search result)
            try:
                if "search_skills" in self.test_results["skills"] and self.test_results["skills"]["search_skills"]["status"] == "✅ PASS":
                    search_results = await client.search_skills("python", limit=1)
                    if search_results:
                        skill_detail = await client.get_skill_by_id(search_results[0].id)
                        self.test_results["skills"]["get_skill_by_id"] = {
                            "status": "✅ PASS",
                            "skill_name": skill_detail.name,
                            "has_description": bool(skill_detail.description)
                        }
                        logger.info(f"✅ get_skill_by_id: {skill_detail.name}")
                    else:
                        raise Exception("No skills found in search")
                else:
                    raise Exception("Search skills failed, cannot test get_skill_by_id")
            except Exception as e:
                self.test_results["skills"]["get_skill_by_id"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_skill_by_id: {e}")
            
            # Test 3: Get Skills Version Metadata
            try:
                metadata = await client.get_version_metadata()
                self.test_results["skills"]["get_version_metadata"] = {
                    "status": "✅ PASS",
                    "version": metadata.version,
                    "skill_count": metadata.skillCount,
                    "language_support": len(metadata.languageSupport)
                }
                logger.info(f"✅ get_version_metadata: Version {metadata.version}, {metadata.skillCount} skills")
            except Exception as e:
                self.test_results["skills"]["get_version_metadata"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_version_metadata: {e}")
            
            # Test 4: Get Skills Metadata
            try:
                metadata = await client.get_skills_metadata()
                self.test_results["skills"]["get_skills_metadata"] = {
                    "status": "✅ PASS",
                    "has_data": bool(metadata)
                }
                logger.info(f"✅ get_skills_metadata: Retrieved metadata")
            except Exception as e:
                self.test_results["skills"]["get_skills_metadata"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_skills_metadata: {e}")
            
            # Test 5: Get Skill Categories
            try:
                categories = await client.get_skill_categories()
                self.test_results["skills"]["get_skill_categories"] = {
                    "status": "✅ PASS",
                    "category_count": len(categories)
                }
                logger.info(f"✅ get_skill_categories: Found {len(categories)} categories")
            except Exception as e:
                self.test_results["skills"]["get_skill_categories"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_skill_categories: {e}")
            
            # Test 6: Get Related Skills
            try:
                if "search_skills" in self.test_results["skills"] and self.test_results["skills"]["search_skills"]["status"] == "✅ PASS":
                    search_results = await client.search_skills("python", limit=1)
                    if search_results:
                        related = await client.get_related_skills(search_results[0].id, limit=5)
                        self.test_results["skills"]["get_related_skills"] = {
                            "status": "✅ PASS",
                            "related_count": len(related)
                        }
                        logger.info(f"✅ get_related_skills: Found {len(related)} related skills")
                    else:
                        raise Exception("No skills found for related test")
                else:
                    raise Exception("Search skills failed, cannot test related skills")
            except Exception as e:
                self.test_results["skills"]["get_related_skills"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_related_skills: {e}")
            
            # Test 7: Extract Skills from Text (simple)
            try:
                test_text = "We need a software engineer with Python, JavaScript, and machine learning experience."
                extracted = await client.extract_skills_from_text_simple(test_text)
                self.test_results["skills"]["extract_skills_simple"] = {
                    "status": "✅ PASS",
                    "extracted_count": len(extracted),
                    "sample_skills": [skill.skill.name for skill in extracted[:3]]
                }
                logger.info(f"✅ extract_skills_simple: Extracted {len(extracted)} skills")
                for skill in extracted[:3]:
                    logger.info(f"   - {skill.skill.name} (confidence: {skill.confidence:.2f})")
            except Exception as e:
                self.test_results["skills"]["extract_skills_simple"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ extract_skills_simple: {e}")
            
            # Test 8: Extract Skills from Text (with threshold)
            try:
                test_text = "We need a software engineer with Python, JavaScript, and machine learning experience."
                extracted = await client.extract_skills_from_text(test_text, confidence_threshold=0.7)
                self.test_results["skills"]["extract_skills_with_threshold"] = {
                    "status": "✅ PASS",
                    "extracted_count": len(extracted)
                }
                logger.info(f"✅ extract_skills_with_threshold: Extracted {len(extracted)} high-confidence skills")
            except Exception as e:
                self.test_results["skills"]["extract_skills_with_threshold"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ extract_skills_with_threshold: {e}")
            
            # Test 9: Bulk Retrieve Skills
            try:
                if "search_skills" in self.test_results["skills"] and self.test_results["skills"]["search_skills"]["status"] == "✅ PASS":
                    search_results = await client.search_skills("programming", limit=3)
                    if len(search_results) >= 2:
                        skill_ids = [skill.id for skill in search_results[:2]]
                        bulk_results = await client.bulk_retrieve_skills(skill_ids)
                        self.test_results["skills"]["bulk_retrieve_skills"] = {
                            "status": "✅ PASS",
                            "requested": len(skill_ids),
                            "retrieved": len(bulk_results)
                        }
                        logger.info(f"✅ bulk_retrieve_skills: Retrieved {len(bulk_results)}/{len(skill_ids)} skills")
                    else:
                        raise Exception("Not enough skills found for bulk test")
                else:
                    raise Exception("Search skills failed, cannot test bulk retrieve")
            except Exception as e:
                self.test_results["skills"]["bulk_retrieve_skills"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ bulk_retrieve_skills: {e}")
            
            # Test 10: Get Skills by IDs (using get_skills_by_ids)
            try:
                if "search_skills" in self.test_results["skills"] and self.test_results["skills"]["search_skills"]["status"] == "✅ PASS":
                    search_results = await client.search_skills("programming", limit=3)
                    if len(search_results) >= 2:
                        skill_ids = [skill.id for skill in search_results[:2]]
                        multiple_results = await client.get_skills_by_ids(skill_ids)
                        self.test_results["skills"]["get_skills_by_ids"] = {
                            "status": "✅ PASS",
                            "requested": len(skill_ids),
                            "retrieved": len(multiple_results)
                        }
                        logger.info(f"✅ get_skills_by_ids: Retrieved {len(multiple_results)}/{len(skill_ids)} skills")
                    else:
                        raise Exception("Not enough skills found for multiple IDs test")
                else:
                    raise Exception("Search skills failed, cannot test get_skills_by_ids")
            except Exception as e:
                self.test_results["skills"]["get_skills_by_ids"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_skills_by_ids: {e}")

    async def test_titles_endpoints(self):
        """Test all Titles API endpoints."""
        logger.info("\n🧪 Testing Titles API Endpoints")
        logger.info("=" * 50)
        
        async with TitlesAPIClient() as client:
            # Test 1: Search Titles
            try:
                results = await client.search_titles("engineer", limit=5)
                self.test_results["titles"]["search_titles"] = {
                    "status": "✅ PASS",
                    "count": len(results),
                    "sample": results[0].name if results else None
                }
                logger.info(f"✅ search_titles: Found {len(results)} titles")
                if results:
                    logger.info(f"   Sample: {results[0].name}")
            except Exception as e:
                self.test_results["titles"]["search_titles"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ search_titles: {e}")
            
            # Test 2: Get Title by ID
            try:
                if "search_titles" in self.test_results["titles"] and self.test_results["titles"]["search_titles"]["status"] == "✅ PASS":
                    search_results = await client.search_titles("engineer", limit=1)
                    if search_results:
                        title_detail = await client.get_title_by_id(search_results[0].id)
                        self.test_results["titles"]["get_title_by_id"] = {
                            "status": "✅ PASS",
                            "title_name": title_detail.name,
                            "has_children": bool(title_detail.children)
                        }
                        logger.info(f"✅ get_title_by_id: {title_detail.name}")
                    else:
                        raise Exception("No titles found in search")
                else:
                    raise Exception("Search titles failed, cannot test get_title_by_id")
            except Exception as e:
                self.test_results["titles"]["get_title_by_id"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_title_by_id: {e}")
            
            # Test 3: Normalize Title
            try:
                test_title = "Software Engineer"
                normalized = await client.normalize_title(test_title)
                self.test_results["titles"]["normalize_title"] = {
                    "status": "✅ PASS",
                    "original": test_title,
                    "normalized": normalized.name,
                    "confidence": normalized.confidence
                }
                logger.info(f"✅ normalize_title: '{test_title}' → '{normalized.name}' (confidence: {normalized.confidence:.2f})")
            except Exception as e:
                self.test_results["titles"]["normalize_title"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ normalize_title: {e}")
            
            # Test 4: Get Title Hierarchy
            try:
                if "search_titles" in self.test_results["titles"] and self.test_results["titles"]["search_titles"]["status"] == "✅ PASS":
                    search_results = await client.search_titles("engineer", limit=1)
                    if search_results:
                        hierarchy = await client.get_title_hierarchy(search_results[0].id)
                        self.test_results["titles"]["get_title_hierarchy"] = {
                            "status": "✅ PASS",
                            "has_data": bool(hierarchy)
                        }
                        logger.info(f"✅ get_title_hierarchy: Retrieved hierarchy data")
                    else:
                        raise Exception("No titles found for hierarchy test")
                else:
                    raise Exception("Search titles failed, cannot test hierarchy")
            except Exception as e:
                self.test_results["titles"]["get_title_hierarchy"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_title_hierarchy: {e}")
            
            # Test 5: Get Titles Metadata
            try:
                metadata = await client.get_titles_metadata()
                self.test_results["titles"]["get_titles_metadata"] = {
                    "status": "✅ PASS",
                    "has_data": bool(metadata)
                }
                logger.info(f"✅ get_titles_metadata: Retrieved metadata")
            except Exception as e:
                self.test_results["titles"]["get_titles_metadata"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_titles_metadata: {e}")
            
            # Test 6: Get Version Metadata
            try:
                version_metadata = await client.get_version_metadata()
                self.test_results["titles"]["get_version_metadata"] = {
                    "status": "✅ PASS",
                    "version": version_metadata.version,
                    "title_count": version_metadata.titleCount
                }
                logger.info(f"✅ get_version_metadata: Version {version_metadata.version}, {version_metadata.titleCount} titles")
            except Exception as e:
                self.test_results["titles"]["get_version_metadata"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_version_metadata: {e}")
            
            # Test 7: Get General Metadata
            try:
                general_metadata = await client.get_general_metadata()
                self.test_results["titles"]["get_general_metadata"] = {
                    "status": "✅ PASS",
                    "latest_version": general_metadata.latestVersion
                }
                logger.info(f"✅ get_general_metadata: Latest version {general_metadata.latestVersion}")
            except Exception as e:
                self.test_results["titles"]["get_general_metadata"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ get_general_metadata: {e}")
            
            # Test 8: Bulk Retrieve Titles
            try:
                if "search_titles" in self.test_results["titles"] and self.test_results["titles"]["search_titles"]["status"] == "✅ PASS":
                    search_results = await client.search_titles("engineer", limit=3)
                    if len(search_results) >= 2:
                        title_ids = [title.id for title in search_results[:2]]
                        bulk_results = await client.bulk_retrieve_titles(title_ids)
                        self.test_results["titles"]["bulk_retrieve_titles"] = {
                            "status": "✅ PASS",
                            "requested": len(title_ids),
                            "retrieved": len(bulk_results)
                        }
                        logger.info(f"✅ bulk_retrieve_titles: Retrieved {len(bulk_results)}/{len(title_ids)} titles")
                    else:
                        raise Exception("Not enough titles found for bulk test")
                else:
                    raise Exception("Search titles failed, cannot test bulk retrieve")
            except Exception as e:
                self.test_results["titles"]["bulk_retrieve_titles"] = {"status": f"❌ FAIL: {str(e)[:60]}"}
                logger.error(f"❌ bulk_retrieve_titles: {e}")

    def print_summary(self):
        """Print a comprehensive test summary."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 COMPREHENSIVE API ENDPOINT TEST RESULTS")
        logger.info("=" * 70)
        
        # Skills API Summary
        logger.info("\n🔧 SKILLS API ENDPOINTS")
        logger.info("-" * 30)
        skills_passed = 0
        skills_total = 0
        for endpoint, result in self.test_results["skills"].items():
            status = result["status"]
            logger.info(f"{status:<15} {endpoint}")
            skills_total += 1
            if status.startswith("✅"):
                skills_passed += 1
        
        # Titles API Summary  
        logger.info("\n📋 TITLES API ENDPOINTS")
        logger.info("-" * 30)
        titles_passed = 0
        titles_total = 0
        for endpoint, result in self.test_results["titles"].items():
            status = result["status"]
            logger.info(f"{status:<15} {endpoint}")
            titles_total += 1
            if status.startswith("✅"):
                titles_passed += 1
        
        # Overall Summary
        total_passed = skills_passed + titles_passed
        total_tests = skills_total + titles_total
        success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        logger.info("\n📈 OVERALL SUMMARY")
        logger.info("-" * 20)
        logger.info(f"Skills API:     {skills_passed}/{skills_total} endpoints working ({(skills_passed/skills_total)*100:.1f}%)")
        logger.info(f"Titles API:     {titles_passed}/{titles_total} endpoints working ({(titles_passed/titles_total)*100:.1f}%)")
        logger.info(f"TOTAL:          {total_passed}/{total_tests} endpoints working ({success_rate:.1f}%)")
        
        # Key Features Status
        logger.info("\n🌟 KEY FEATURES STATUS")
        logger.info("-" * 25)
        
        # Skills extract functionality
        skills_extract_working = (
            self.test_results["skills"].get("extract_skills_simple", {}).get("status", "").startswith("✅") or
            self.test_results["skills"].get("extract_skills_with_threshold", {}).get("status", "").startswith("✅")
        )
        logger.info(f"{'✅' if skills_extract_working else '❌'} Skills Extraction from Text")
        
        # Title normalization
        title_normalize_working = self.test_results["titles"].get("normalize_title", {}).get("status", "").startswith("✅")
        logger.info(f"{'✅' if title_normalize_working else '❌'} Title Normalization")
        
        # Bulk operations
        bulk_skills_working = self.test_results["skills"].get("bulk_retrieve_skills", {}).get("status", "").startswith("✅")
        bulk_titles_working = self.test_results["titles"].get("bulk_retrieve_titles", {}).get("status", "").startswith("✅")
        logger.info(f"{'✅' if bulk_skills_working else '❌'} Skills Bulk Retrieval")
        logger.info(f"{'✅' if bulk_titles_working else '❌'} Titles Bulk Retrieval")
        
        # Version metadata
        skills_meta_working = self.test_results["skills"].get("get_version_metadata", {}).get("status", "").startswith("✅")
        titles_meta_working = self.test_results["titles"].get("get_version_metadata", {}).get("status", "").startswith("✅")
        logger.info(f"{'✅' if skills_meta_working else '❌'} API Version Metadata")
        
        logger.info("\n" + "=" * 70)

async def main():
    """Run comprehensive endpoint testing."""
    logger.info("🚀 Starting Comprehensive API Endpoint Testing")
    logger.info("Testing all implemented Skills and Titles API endpoints...")
    
    tester = EndpointTester()
    
    # Test all endpoints
    await tester.test_skills_endpoints()
    await tester.test_titles_endpoints()
    
    # Print comprehensive summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())