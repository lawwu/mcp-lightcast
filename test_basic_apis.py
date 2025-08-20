#!/usr/bin/env python3
"""
Test script for basic Lightcast API endpoints (Skills and Titles APIs).
Tests endpoints that work with emsi_open scope.
"""

import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.mcp_lightcast.apis.skills import SkillsAPIClient
from src.mcp_lightcast.apis.titles import TitlesAPIClient


class BasicAPITester:
    """Test runner for basic API endpoints that work with emsi_open scope."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.results_file = "basic_api_test_results.txt"
    
    def log_result(self, api: str, endpoint: str, success: bool, error: str = None, response_sample: Any = None):
        """Log test result."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "api": api,
            "endpoint": endpoint,
            "success": success,
            "error": error,
            "response_sample": str(response_sample)[:200] + "..." if response_sample and len(str(response_sample)) > 200 else response_sample
        }
        self.results.append(result)
        
        # Print real-time status
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} {api} - {endpoint}")
        if error:
            print(f"   Error: {error}")
    
    async def test_skills_api(self):
        """Test Skills API endpoints."""
        print("\n🔧 Testing Skills API (Basic Access)...")
        
        try:
            async with SkillsAPIClient() as client:
                # Test search_skills
                try:
                    results = await client.search_skills("python", limit=5)
                    self.log_result("Skills", "search_skills", True, response_sample=f"Found {len(results)} skills")
                except Exception as e:
                    self.log_result("Skills", "search_skills", False, str(e))
                
                # Test get_skills_metadata
                try:
                    result = await client.get_skills_metadata()
                    self.log_result("Skills", "get_skills_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Skills", "get_skills_metadata", False, str(e))
                
                # Test get_version_metadata
                try:
                    result = await client.get_version_metadata()
                    self.log_result("Skills", "get_version_metadata", True, response_sample=result.model_dump() if hasattr(result, 'model_dump') else result)
                except Exception as e:
                    self.log_result("Skills", "get_version_metadata", False, str(e))
                
                # Test get_skill_by_id (using a common skill ID)
                try:
                    result = await client.get_skill_by_id("KS120076")  # Python skill
                    self.log_result("Skills", "get_skill_by_id", True, response_sample=result.model_dump() if hasattr(result, 'model_dump') else result)
                except Exception as e:
                    self.log_result("Skills", "get_skill_by_id", False, str(e))
                
                # Test get_skill_categories
                try:
                    result = await client.get_skill_categories()
                    self.log_result("Skills", "get_skill_categories", True, response_sample=f"Found {len(result)} categories" if isinstance(result, list) else result)
                except Exception as e:
                    self.log_result("Skills", "get_skill_categories", False, str(e))
                
                # Test extract_skills_from_text
                try:
                    result = await client.extract_skills_from_text("I have experience with Python, Java, and machine learning")
                    self.log_result("Skills", "extract_skills_from_text", True, response_sample=f"Extracted {len(result)} skills" if isinstance(result, list) else result)
                except Exception as e:
                    self.log_result("Skills", "extract_skills_from_text", False, str(e))
                
        except Exception as e:
            self.log_result("Skills", "CLIENT_INITIALIZATION", False, str(e))
    
    async def test_titles_api(self):
        """Test Titles API endpoints."""
        print("\n📋 Testing Titles API (Basic Access)...")
        
        try:
            async with TitlesAPIClient() as client:
                # Test search_titles
                try:
                    results = await client.search_titles("software engineer", limit=5)
                    self.log_result("Titles", "search_titles", True, response_sample=f"Found {len(results)} titles")
                except Exception as e:
                    self.log_result("Titles", "search_titles", False, str(e))
                
                # Test get_titles_metadata
                try:
                    result = await client.get_titles_metadata()
                    self.log_result("Titles", "get_titles_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Titles", "get_titles_metadata", False, str(e))
                
                # Test get_version_metadata
                try:
                    result = await client.get_version_metadata()
                    self.log_result("Titles", "get_version_metadata", True, response_sample=result.model_dump() if hasattr(result, 'model_dump') else result)
                except Exception as e:
                    self.log_result("Titles", "get_version_metadata", False, str(e))
                
                # Test get_title_by_id (using a common title ID)
                try:
                    result = await client.get_title_by_id("ET4E3EE5206D4BCDB")  # Common software engineer title
                    self.log_result("Titles", "get_title_by_id", True, response_sample=result.model_dump() if hasattr(result, 'model_dump') else result)
                except Exception as e:
                    self.log_result("Titles", "get_title_by_id", False, str(e))
                
                # Test normalize_title
                try:
                    result = await client.normalize_title("Software Developer")
                    self.log_result("Titles", "normalize_title", True, response_sample=result)
                except Exception as e:
                    self.log_result("Titles", "normalize_title", False, str(e))
                
        except Exception as e:
            self.log_result("Titles", "CLIENT_INITIALIZATION", False, str(e))
    
    def write_results_to_file(self):
        """Write test results to file."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Calculate summary statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        with open(self.results_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("BASIC LIGHTCAST API ENDPOINTS TEST RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Test Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {duration}\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Successful: {successful_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {success_rate:.1f}%\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("NOTE: This test suite only covers basic APIs (Skills and Titles)\n")
            f.write("that work with the 'emsi_open' scope. Premium APIs require upgraded\n")
            f.write("Lightcast account with premium scopes.\n\n")
            
            # Group results by API
            api_groups = {}
            for result in self.results:
                api = result["api"]
                if api not in api_groups:
                    api_groups[api] = []
                api_groups[api].append(result)
            
            # Write results for each API
            for api, api_results in api_groups.items():
                f.write(f"\n{api} API RESULTS\n")
                f.write("-" * 40 + "\n")
                
                api_success = sum(1 for r in api_results if r["success"])
                api_total = len(api_results)
                api_rate = (api_success / api_total * 100) if api_total > 0 else 0
                
                f.write(f"API Success Rate: {api_success}/{api_total} ({api_rate:.1f}%)\n\n")
                
                for result in api_results:
                    status = "SUCCESS" if result["success"] else "FAILED"
                    f.write(f"[{status}] {result['endpoint']}\n")
                    f.write(f"  Timestamp: {result['timestamp']}\n")
                    
                    if result["error"]:
                        f.write(f"  Error: {result['error']}\n")
                    
                    if result["response_sample"]:
                        f.write(f"  Sample Response: {result['response_sample']}\n")
                    
                    f.write("\n")
                
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF TEST RESULTS\n")
            f.write("=" * 80 + "\n")
        
        print(f"\n📄 Results written to: {self.results_file}")
        print(f"📊 Summary: {successful_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    async def run_all_tests(self):
        """Run all basic API tests."""
        print("🚀 Starting Basic API Endpoint Testing...")
        print("📝 Testing only APIs available with 'emsi_open' scope")
        print(f"📝 Results will be written to: {self.results_file}")
        
        await self.test_skills_api()
        await self.test_titles_api()
        
        self.write_results_to_file()
        print("\n✅ All basic API tests completed!")
        
        # Show upgrade information
        print(f"\n💡 For Premium API Access:")
        print(f"   • Contact Lightcast Sales to upgrade your plan")
        print(f"   • Premium APIs include: Classification, Similarity, Benchmarks, Career Pathways, Job Postings")
        print(f"   • Premium features: Job title normalization, skill extraction, salary benchmarks, career analysis")


async def main():
    """Main test runner."""
    tester = BasicAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())