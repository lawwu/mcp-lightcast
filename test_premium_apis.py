#!/usr/bin/env python3
"""
Test script for all premium Lightcast API endpoints.
Tests each endpoint and writes results to premium_api_test_results.txt
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

from src.mcp_lightcast.apis.classification import ClassificationAPIClient
from src.mcp_lightcast.apis.similarity import SimilarityAPIClient
from src.mcp_lightcast.apis.occupation_benchmark import OccupationBenchmarkAPIClient
from src.mcp_lightcast.apis.career_pathways import CareerPathwaysAPIClient
from src.mcp_lightcast.apis.job_postings import JobPostingsAPIClient


class PremiumAPITester:
    """Test runner for all premium API endpoints."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.results_file = "premium_api_test_results.txt"
    
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
    
    async def test_classification_api(self):
        """Test Classification API endpoints."""
        print("\n🔍 Testing Classification API...")
        
        try:
            async with ClassificationAPIClient() as client:
                # Test map_concepts_to_occupations
                try:
                    result = await client.map_concepts_to_occupations(
                        concepts=["software engineer", "data scientist"],
                        limit=5
                    )
                    self.log_result("Classification", "map_concepts_to_occupations", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "map_concepts_to_occupations", False, str(e))
                
                # Test normalize_job_title
                try:
                    result = await client.normalize_job_title("Software Developer")
                    self.log_result("Classification", "normalize_job_title", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "normalize_job_title", False, str(e))
                
                # Test extract_skills_from_description
                try:
                    result = await client.extract_skills_from_description(
                        "We are looking for a Python developer with experience in machine learning and AWS."
                    )
                    self.log_result("Classification", "extract_skills_from_description", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "extract_skills_from_description", False, str(e))
                
                # Test classify_occupation_level
                try:
                    result = await client.classify_occupation_level("Senior Software Engineer")
                    self.log_result("Classification", "classify_occupation_level", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "classify_occupation_level", False, str(e))
                
                # Test search_occupations
                try:
                    result = await client.search_occupations("software", limit=5)
                    self.log_result("Classification", "search_occupations", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "search_occupations", False, str(e))
                
                # Test get_soc_metadata
                try:
                    result = await client.get_soc_metadata()
                    self.log_result("Classification", "get_soc_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "get_soc_metadata", False, str(e))
                
                # Test get_classification_metadata
                try:
                    result = await client.get_classification_metadata()
                    self.log_result("Classification", "get_classification_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Classification", "get_classification_metadata", False, str(e))
                
        except Exception as e:
            self.log_result("Classification", "CLIENT_INITIALIZATION", False, str(e))
    
    async def test_similarity_api(self):
        """Test Similarity API endpoints."""
        print("\n🔗 Testing Similarity API...")
        
        try:
            async with SimilarityAPIClient() as client:
                # Test find_similar_occupations (using a common occupation ID)
                try:
                    result = await client.find_similar_occupations("15-1254.00", limit=5)  # Software developers
                    self.log_result("Similarity", "find_similar_occupations", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "find_similar_occupations", False, str(e))
                
                # Test find_similar_skills (using a common skill ID)
                try:
                    result = await client.find_similar_skills("KS120076", limit=5)  # Python (common skill ID)
                    self.log_result("Similarity", "find_similar_skills", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "find_similar_skills", False, str(e))
                
                # Test get_occupation_skills
                try:
                    result = await client.get_occupation_skills("15-1254.00", limit=10)
                    self.log_result("Similarity", "get_occupation_skills", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "get_occupation_skills", False, str(e))
                
                # Test find_occupations_by_skills
                try:
                    result = await client.find_occupations_by_skills(["KS120076", "KS125LS6YNX1MTGHTCG8"], limit=5)
                    self.log_result("Similarity", "find_occupations_by_skills", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "find_occupations_by_skills", False, str(e))
                
                # Test calculate_skill_gaps
                try:
                    result = await client.calculate_skill_gaps(
                        current_skills=["KS120076"],
                        target_occupation_id="15-1254.00"
                    )
                    self.log_result("Similarity", "calculate_skill_gaps", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "calculate_skill_gaps", False, str(e))
                
                # Test compare_occupations
                try:
                    result = await client.compare_occupations("15-1254.00", "15-1255.00")
                    self.log_result("Similarity", "compare_occupations", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "compare_occupations", False, str(e))
                
                # Test get_similarity_metadata
                try:
                    result = await client.get_similarity_metadata()
                    self.log_result("Similarity", "get_similarity_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Similarity", "get_similarity_metadata", False, str(e))
                
        except Exception as e:
            self.log_result("Similarity", "CLIENT_INITIALIZATION", False, str(e))
    
    async def test_occupation_benchmark_api(self):
        """Test Occupation Benchmark API endpoints."""
        print("\n📊 Testing Occupation Benchmark API...")
        
        try:
            async with OccupationBenchmarkAPIClient() as client:
                # Test get_occupation_benchmark
                try:
                    result = await client.get_occupation_benchmark(
                        occupation_id="15-1254.00",
                        metrics=["salary", "employment"]
                    )
                    self.log_result("Occupation Benchmark", "get_occupation_benchmark", True, response_sample=result)
                except Exception as e:
                    self.log_result("Occupation Benchmark", "get_occupation_benchmark", False, str(e))
                
                # Test get_salary_benchmarks
                try:
                    result = await client.get_salary_benchmarks(
                        occupation_ids=["15-1254.00", "15-1255.00"]
                    )
                    self.log_result("Occupation Benchmark", "get_salary_benchmarks", True, response_sample=result)
                except Exception as e:
                    self.log_result("Occupation Benchmark", "get_salary_benchmarks", False, str(e))
                
                # Test get_skill_demand_benchmarks
                try:
                    result = await client.get_skill_demand_benchmarks(
                        skill_ids=["KS120076"],
                        limit=10
                    )
                    self.log_result("Occupation Benchmark", "get_skill_demand_benchmarks", True, response_sample=result)
                except Exception as e:
                    self.log_result("Occupation Benchmark", "get_skill_demand_benchmarks", False, str(e))
                
                # Test compare_occupations_benchmark
                try:
                    result = await client.compare_occupations_benchmark(
                        occupation_ids=["15-1254.00", "15-1255.00"],
                        metrics=["salary", "employment"]
                    )
                    self.log_result("Occupation Benchmark", "compare_occupations_benchmark", True, response_sample=result)
                except Exception as e:
                    self.log_result("Occupation Benchmark", "compare_occupations_benchmark", False, str(e))
                
                # Test get_employment_trends
                try:
                    result = await client.get_employment_trends("15-1254.00")
                    self.log_result("Occupation Benchmark", "get_employment_trends", True, response_sample=result)
                except Exception as e:
                    self.log_result("Occupation Benchmark", "get_employment_trends", False, str(e))
                
                # Test get_benchmark_metadata
                try:
                    result = await client.get_benchmark_metadata()
                    self.log_result("Occupation Benchmark", "get_benchmark_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Occupation Benchmark", "get_benchmark_metadata", False, str(e))
                
        except Exception as e:
            self.log_result("Occupation Benchmark", "CLIENT_INITIALIZATION", False, str(e))
    
    async def test_career_pathways_api(self):
        """Test Career Pathways API endpoints."""
        print("\n🛤️ Testing Career Pathways API...")
        
        try:
            async with CareerPathwaysAPIClient() as client:
                # Test analyze_career_pathway
                try:
                    result = await client.analyze_career_pathway(
                        from_occupation_id="15-1254.00",
                        to_occupation_id="11-3021.00"  # Computer and Information Systems Managers
                    )
                    self.log_result("Career Pathways", "analyze_career_pathway", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "analyze_career_pathway", False, str(e))
                
                # Test discover_career_pathways
                try:
                    result = await client.discover_career_pathways(
                        occupation_id="15-1254.00",
                        pathway_type="advancement",
                        limit=5
                    )
                    self.log_result("Career Pathways", "discover_career_pathways", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "discover_career_pathways", False, str(e))
                
                # Test get_skill_transition_map
                try:
                    result = await client.get_skill_transition_map(
                        from_occupation_id="15-1254.00",
                        to_occupation_id="11-3021.00"
                    )
                    self.log_result("Career Pathways", "get_skill_transition_map", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "get_skill_transition_map", False, str(e))
                
                # Test get_pathway_recommendations
                try:
                    result = await client.get_pathway_recommendations(
                        current_occupation_id="15-1254.00",
                        career_goals=["advancement", "salary_increase"]
                    )
                    self.log_result("Career Pathways", "get_pathway_recommendations", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "get_pathway_recommendations", False, str(e))
                
                # Test validate_pathway_feasibility
                try:
                    result = await client.validate_pathway_feasibility(
                        pathway_steps=["15-1254.00", "11-3021.00"]
                    )
                    self.log_result("Career Pathways", "validate_pathway_feasibility", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "validate_pathway_feasibility", False, str(e))
                
                # Test get_trending_pathways
                try:
                    result = await client.get_trending_pathways(limit=5)
                    self.log_result("Career Pathways", "get_trending_pathways", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "get_trending_pathways", False, str(e))
                
                # Test get_pathways_metadata
                try:
                    result = await client.get_pathways_metadata()
                    self.log_result("Career Pathways", "get_pathways_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Career Pathways", "get_pathways_metadata", False, str(e))
                
        except Exception as e:
            self.log_result("Career Pathways", "CLIENT_INITIALIZATION", False, str(e))
    
    async def test_job_postings_api(self):
        """Test Job Postings API endpoints."""
        print("\n💼 Testing Job Postings API...")
        
        try:
            async with JobPostingsAPIClient() as client:
                # Test search_job_postings
                try:
                    result = await client.search_job_postings(
                        query="software engineer",
                        limit=5
                    )
                    self.log_result("Job Postings", "search_job_postings", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "search_job_postings", False, str(e))
                
                # Test get_posting_statistics
                try:
                    result = await client.get_posting_statistics(
                        occupation_ids=["15-1254.00"]
                    )
                    self.log_result("Job Postings", "get_posting_statistics", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "get_posting_statistics", False, str(e))
                
                # Test analyze_skill_demand
                try:
                    result = await client.analyze_skill_demand(
                        occupation_ids=["15-1254.00"],
                        limit=10
                    )
                    self.log_result("Job Postings", "analyze_skill_demand", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "analyze_skill_demand", False, str(e))
                
                # Test get_salary_insights
                try:
                    result = await client.get_salary_insights(
                        occupation_ids=["15-1254.00"]
                    )
                    self.log_result("Job Postings", "get_salary_insights", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "get_salary_insights", False, str(e))
                
                # Test analyze_market_trends
                try:
                    result = await client.analyze_market_trends(
                        occupation_ids=["15-1254.00"]
                    )
                    self.log_result("Job Postings", "analyze_market_trends", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "analyze_market_trends", False, str(e))
                
                # Test extract_skills_from_posting
                try:
                    result = await client.extract_skills_from_posting(
                        "We are looking for a Python developer with React experience and AWS knowledge."
                    )
                    self.log_result("Job Postings", "extract_skills_from_posting", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "extract_skills_from_posting", False, str(e))
                
                # Test get_company_insights
                try:
                    result = await client.get_company_insights("Google")
                    self.log_result("Job Postings", "get_company_insights", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "get_company_insights", False, str(e))
                
                # Test get_postings_metadata
                try:
                    result = await client.get_postings_metadata()
                    self.log_result("Job Postings", "get_postings_metadata", True, response_sample=result)
                except Exception as e:
                    self.log_result("Job Postings", "get_postings_metadata", False, str(e))
                
        except Exception as e:
            self.log_result("Job Postings", "CLIENT_INITIALIZATION", False, str(e))
    
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
            f.write("PREMIUM LIGHTCAST API ENDPOINTS TEST RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Test Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {duration}\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Successful: {successful_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {success_rate:.1f}%\n")
            f.write("=" * 80 + "\n\n")
            
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
        """Run all premium API tests."""
        print("🚀 Starting Premium API Endpoint Testing...")
        print(f"📝 Results will be written to: {self.results_file}")
        
        await self.test_classification_api()
        await self.test_similarity_api()
        await self.test_occupation_benchmark_api()
        await self.test_career_pathways_api()
        await self.test_job_postings_api()
        
        self.write_results_to_file()
        print("\n✅ All tests completed!")


async def main():
    """Main test runner."""
    tester = PremiumAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())