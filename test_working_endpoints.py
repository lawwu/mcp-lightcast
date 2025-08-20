#!/usr/bin/env python3
"""Test the working endpoints that we discovered."""

import asyncio
import logging
from src.mcp_lightcast.apis.skills import SkillsAPIClient
from src.mcp_lightcast.apis.titles import TitlesAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_working_skills_endpoints():
    """Test the Skills API endpoints that are confirmed working."""
    logger.info("🧪 Testing Working Skills API Endpoints")
    logger.info("=" * 50)
    
    async with SkillsAPIClient() as client:
        # Test 1: Search Skills (confirmed working)
        try:
            results = await client.search_skills("python programming", limit=5)
            logger.info(f"✅ search_skills: Found {len(results)} skills")
            for i, skill in enumerate(results[:3], 1):
                logger.info(f"   {i}. {skill.name} (ID: {skill.id})")
            
            if results:
                test_skill_id = results[0].id
                test_skill_name = results[0].name
                
                # Test 2: Get Skill by ID (fixed URL)
                try:
                    skill_detail = await client.get_skill_by_id(test_skill_id)
                    logger.info(f"✅ get_skill_by_id: Retrieved '{skill_detail.name}'")
                    logger.info(f"   Description: {skill_detail.description[:100] if skill_detail.description else 'None'}...")
                except Exception as e:
                    logger.error(f"❌ get_skill_by_id: {e}")
                
                # Test 3: Get Related Skills (fixed URL)
                try:
                    related = await client.get_related_skills(test_skill_id, limit=3)
                    logger.info(f"✅ get_related_skills: Found {len(related)} related skills for '{test_skill_name}'")
                    for skill in related:
                        logger.info(f"   - {skill.name}")
                except Exception as e:
                    logger.error(f"❌ get_related_skills: {e}")
        
        except Exception as e:
            logger.error(f"❌ search_skills: {e}")
            return
        
        # Test 4: Version Metadata (confirmed working)
        try:
            metadata = await client.get_version_metadata()
            logger.info(f"✅ get_version_metadata: Version {metadata.version}, {metadata.skillCount} skills")
            logger.info(f"   Language support: {', '.join(metadata.languageSupport)}")
            logger.info(f"   Skill types: {len(metadata.types)} types available")
        except Exception as e:
            logger.error(f"❌ get_version_metadata: {e}")
        
        # Test 5: Bulk Retrieve (confirmed working)
        try:
            search_results = await client.search_skills("programming", limit=3)
            if len(search_results) >= 2:
                skill_ids = [skill.id for skill in search_results[:2]]
                bulk_results = await client.bulk_retrieve_skills(skill_ids)
                logger.info(f"✅ bulk_retrieve_skills: Retrieved {len(bulk_results)}/{len(skill_ids)} skills")
                for skill in bulk_results:
                    logger.info(f"   - {skill.name}")
            else:
                logger.warning("⚠️  Not enough skills found for bulk test")
        except Exception as e:
            logger.error(f"❌ bulk_retrieve_skills: {e}")
        
        # Test 6: Skills Extract (test simple format)
        try:
            test_text = "We need a software engineer with Python and JavaScript experience"
            extracted = await client.extract_skills_from_text_simple(test_text)
            logger.info(f"✅ extract_skills_simple: Extracted {len(extracted)} skills from text")
            for skill in extracted[:3]:
                logger.info(f"   - {skill.skill.name} (confidence: {skill.confidence:.2f})")
        except Exception as e:
            logger.error(f"❌ extract_skills_simple: {e}")

async def test_working_titles_endpoints():
    """Test the Titles API endpoints that are confirmed working."""
    logger.info("\n🧪 Testing Working Titles API Endpoints")
    logger.info("=" * 50)
    
    async with TitlesAPIClient() as client:
        # Test 1: Search Titles (confirmed working)
        try:
            results = await client.search_titles("software engineer", limit=5)
            logger.info(f"✅ search_titles: Found {len(results)} titles")
            for i, title in enumerate(results[:3], 1):
                logger.info(f"   {i}. {title.name} (ID: {title.id})")
            
            if results:
                test_title_id = results[0].id
                test_title_name = results[0].name
                
                # Test 2: Get Title by ID (fixed URL)
                try:
                    title_detail = await client.get_title_by_id(test_title_id)
                    logger.info(f"✅ get_title_by_id: Retrieved '{title_detail.name}'")
                    logger.info(f"   Type: {title_detail.type}")
                    logger.info(f"   Has children: {bool(title_detail.children)}")
                except Exception as e:
                    logger.error(f"❌ get_title_by_id: {e}")
                
                # Test 3: Get Title Hierarchy (fixed URL)
                try:
                    hierarchy = await client.get_title_hierarchy(test_title_id)
                    logger.info(f"✅ get_title_hierarchy: Retrieved hierarchy for '{test_title_name}'")
                    logger.info(f"   Hierarchy data available: {bool(hierarchy)}")
                except Exception as e:
                    logger.error(f"❌ get_title_hierarchy: {e}")
        
        except Exception as e:
            logger.error(f"❌ search_titles: {e}")
            return
        
        # Test 4: Version Metadata (confirmed working)
        try:
            metadata = await client.get_version_metadata()
            logger.info(f"✅ get_version_metadata: Version {metadata.version}, {metadata.titleCount} titles")
        except Exception as e:
            logger.error(f"❌ get_version_metadata: {e}")
        
        # Test 5: General Metadata (confirmed working)
        try:
            general = await client.get_general_metadata()
            logger.info(f"✅ get_general_metadata: Latest version {general.latestVersion}")
        except Exception as e:
            logger.error(f"❌ get_general_metadata: {e}")
        
        # Test 6: Bulk Retrieve (confirmed working)
        try:
            search_results = await client.search_titles("engineer", limit=3)
            if len(search_results) >= 2:
                title_ids = [title.id for title in search_results[:2]]
                bulk_results = await client.bulk_retrieve_titles(title_ids)
                logger.info(f"✅ bulk_retrieve_titles: Retrieved {len(bulk_results)}/{len(title_ids)} titles")
                for title in bulk_results:
                    logger.info(f"   - {title.name}")
            else:
                logger.warning("⚠️  Not enough titles found for bulk test")
        except Exception as e:
            logger.error(f"❌ bulk_retrieve_titles: {e}")
        
        # Test 7: Normalize Title (test with simple authentication)
        try:
            test_title = "Software Engineer"
            normalized = await client.normalize_title(test_title)
            logger.info(f"✅ normalize_title: '{test_title}' → '{normalized.name}' (confidence: {normalized.confidence:.2f})")
        except Exception as e:
            logger.error(f"❌ normalize_title: {e}")

async def main():
    """Test all working endpoints."""
    logger.info("🚀 Testing Working API Endpoints")
    logger.info("Testing endpoints with corrected URLs and authentication...")
    
    await test_working_skills_endpoints()
    await test_working_titles_endpoints()
    
    logger.info("\n" + "=" * 70)
    logger.info("✨ Testing Complete - Check individual endpoint results above")
    logger.info("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())