"""
Manual API Integration Tests for MCP Lightcast

These tests make real API calls to Lightcast APIs to verify that all endpoints work correctly.
They require valid API credentials and are not run in CI/CD by default.

Run with: make test-apis-manual
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📄 Loaded environment from {env_file}")
    else:
        load_dotenv()  # Load from any .env in current directory or parents
except ImportError:
    print("⚠️  python-dotenv not available - relying on environment variables")

from src.mcp_lightcast.apis.skills import SkillsAPIClient
from src.mcp_lightcast.apis.titles import TitlesAPIClient
from src.mcp_lightcast.apis.classification import ClassificationAPIClient
from src.mcp_lightcast.apis.similarity import SimilarityAPIClient
from src.mcp_lightcast.apis.occupation_benchmark import OccupationBenchmarkAPIClient
from src.mcp_lightcast.apis.career_pathways import CareerPathwaysAPIClient
from src.mcp_lightcast.apis.job_postings import JobPostingsAPIClient
from src.mcp_lightcast.tools.normalize_title_get_skills import TitleNormalizationWorkflow


class APITestResult:
    """Track test results."""
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.passed = 0
        self.failed = 0
        self.expected_failures = 0
        self.errors = []

    def pass_test(self, test_name: str):
        self.passed += 1
        print(f"  ✅ {test_name}")

    def fail_test(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ❌ {test_name}: {error}")

    def expected_fail_test(self, test_name: str, reason: str):
        self.expected_failures += 1
        print(f"  ⚠️ {test_name}: {reason} (expected failure)")

    def summary(self):
        total = self.passed + self.failed + self.expected_failures
        actual_failures = self.failed
        status = "✅" if actual_failures == 0 else "❌"
        print(f"\n{status} {self.api_name}: {self.passed}/{total} tests passed ({self.expected_failures} expected failures)")
        if self.errors:
            print("  Unexpected Errors:")
            for test_name, error in self.errors:
                print(f"    - {test_name}: {error}")


class ManualAPITester:
    """Manual API testing suite."""
    
    def __init__(self):
        self.results = {}
        
    def check_credentials(self) -> bool:
        """Check if API credentials are configured."""
        client_id = os.getenv("LIGHTCAST_CLIENT_ID")
        client_secret = os.getenv("LIGHTCAST_CLIENT_SECRET")
        
        print("🔑 Checking API credentials...")
        
        if not client_id or not client_secret:
            print("❌ Missing API credentials!")
            print("\nPlease configure your Lightcast API credentials:")
            print("1. Create a .env file in the project root:")
            print("   cp .env.example .env")
            print("2. Add your credentials to .env:")
            print("   LIGHTCAST_CLIENT_ID=your_client_id_here")
            print("   LIGHTCAST_CLIENT_SECRET=your_client_secret_here")
            print("3. Or set environment variables directly:")
            print("   export LIGHTCAST_CLIENT_ID=your_client_id_here")
            print("   export LIGHTCAST_CLIENT_SECRET=your_client_secret_here")
            return False
            
        print(f"✅ LIGHTCAST_CLIENT_ID: {client_id[:10]}...")
        print(f"✅ LIGHTCAST_CLIENT_SECRET: [configured]")
        return True

    async def test_skills_api(self) -> APITestResult:
        """Test Skills API endpoints."""
        result = APITestResult("Skills API")
        client = SkillsAPIClient()
        
        try:
            async with client:
                # Test search skills
                try:
                    skills = await client.search_skills("Python", limit=5)
                    if skills and len(skills) > 0:
                        result.pass_test(f"search_skills - Found {len(skills)} skills")
                    else:
                        result.fail_test("search_skills", "No skills returned")
                except Exception as e:
                    result.fail_test("search_skills", str(e))

                # Test get skill by ID (use first skill from search)
                if hasattr(skills, '__len__') and len(skills) > 0:
                    try:
                        skill_detail = await client.get_skill_by_id(skills[0].id)
                        if skill_detail.name:
                            result.pass_test(f"get_skill_by_id - Got {skill_detail.name}")
                        else:
                            result.fail_test("get_skill_by_id", "No skill name returned")
                    except Exception as e:
                        result.fail_test("get_skill_by_id", str(e))

                # Test get skills metadata
                try:
                    metadata = await client.get_skills_metadata()
                    if metadata:
                        result.pass_test("get_skills_metadata - Got metadata")
                    else:
                        result.fail_test("get_skills_metadata", "No metadata returned")
                except Exception as e:
                    result.fail_test("get_skills_metadata", str(e))

                # Test bulk retrieve skills
                if hasattr(skills, '__len__') and len(skills) >= 2:
                    try:
                        skill_ids = [skills[0].id, skills[1].id]
                        bulk_skills = await client.bulk_retrieve_skills(skill_ids)
                        if bulk_skills and len(bulk_skills) >= 2:
                            result.pass_test(f"bulk_retrieve_skills - Got {len(bulk_skills)} skills")
                        else:
                            result.fail_test("bulk_retrieve_skills", f"Expected 2+ skills, got {len(bulk_skills) if bulk_skills else 0}")
                    except Exception as e:
                        result.fail_test("bulk_retrieve_skills", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_titles_api(self) -> APITestResult:
        """Test Titles API endpoints."""
        result = APITestResult("Titles API")
        client = TitlesAPIClient()
        
        try:
            async with client:
                # Test search titles
                try:
                    titles = await client.search_titles("Software Engineer", limit=5)
                    if titles and len(titles) > 0:
                        result.pass_test(f"search_titles - Found {len(titles)} titles")
                    else:
                        result.fail_test("search_titles", "No titles returned")
                except Exception as e:
                    result.fail_test("search_titles", str(e))

                # Test get title by ID
                if hasattr(titles, '__len__') and len(titles) > 0:
                    try:
                        title_detail = await client.get_title_by_id(titles[0].id)
                        if title_detail.name:
                            result.pass_test(f"get_title_by_id - Got {title_detail.name}")
                        else:
                            result.fail_test("get_title_by_id", "No title name returned")
                    except Exception as e:
                        result.fail_test("get_title_by_id", str(e))

                # Test normalize title
                try:
                    normalized = await client.normalize_title("sr software dev")
                    if normalized:
                        result.pass_test("normalize_title - Got normalization result")
                    else:
                        result.fail_test("normalize_title", "No normalization result")
                except Exception as e:
                    result.fail_test("normalize_title", str(e))

                # Test get title hierarchy
                if hasattr(titles, '__len__') and len(titles) > 0:
                    try:
                        hierarchy = await client.get_title_hierarchy(titles[0].id)
                        if hierarchy:
                            result.pass_test("get_title_hierarchy - Got hierarchy")
                        else:
                            result.fail_test("get_title_hierarchy", "No hierarchy returned")
                    except Exception as e:
                        result.fail_test("get_title_hierarchy", str(e))

                # Test get titles metadata
                try:
                    metadata = await client.get_titles_metadata()
                    if metadata:
                        result.pass_test("get_titles_metadata - Got metadata")
                    else:
                        result.fail_test("get_titles_metadata", "No metadata returned")
                except Exception as e:
                    result.fail_test("get_titles_metadata", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_classification_api(self) -> APITestResult:
        """Test Classification API endpoints."""
        result = APITestResult("Classification API")
        client = ClassificationAPIClient()
        
        try:
            async with client:
                # Test extract skills from text
                try:
                    extraction_result = await client.extract_skills_from_text(
                        "I have experience with Python programming, machine learning, and data analysis"
                    )
                    if extraction_result.concepts and len(extraction_result.concepts) > 0:
                        result.pass_test(f"extract_skills_from_text - Found {len(extraction_result.concepts)} skills")
                    else:
                        result.fail_test("extract_skills_from_text", "No skills extracted")
                except Exception as e:
                    result.fail_test("extract_skills_from_text", str(e))

                # Test get available versions
                try:
                    versions = await client.get_available_versions()
                    if versions and len(versions) > 0:
                        result.pass_test(f"get_available_versions - Found {len(versions)} versions")
                    else:
                        result.fail_test("get_available_versions", "No versions returned")
                except Exception as e:
                    result.fail_test("get_available_versions", str(e))

                # Test get version metadata
                try:
                    metadata = await client.get_version_metadata()
                    if metadata:
                        result.pass_test("get_version_metadata - Got metadata")
                    else:
                        result.fail_test("get_version_metadata", "No metadata returned")
                except Exception as e:
                    result.fail_test("get_version_metadata", str(e))

                # Test normalize skill
                try:
                    normalized_skill = await client.normalize_skill("python programming")
                    if normalized_skill:
                        result.pass_test("normalize_skill - Got normalization result")
                    else:
                        result.fail_test("normalize_skill", "No normalization result")
                except Exception as e:
                    result.fail_test("normalize_skill", str(e))

                # Test normalize title
                try:
                    normalized_title = await client.normalize_title("software engineer")
                    if normalized_title:
                        result.pass_test("normalize_title - Got normalization result")
                    else:
                        result.fail_test("normalize_title", "No normalization result")
                except Exception as e:
                    result.fail_test("normalize_title", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_similarity_api(self) -> APITestResult:
        """Test Similarity API endpoints."""
        result = APITestResult("Similarity API")
        client = SimilarityAPIClient()
        
        try:
            async with client:
                # Test get occupation skills
                try:
                    occ_skills = await client.get_occupation_skills("15-1252.00", limit=10)
                    if occ_skills and occ_skills.skills:
                        result.pass_test(f"get_occupation_skills - Found {len(occ_skills.skills)} skills")
                    else:
                        result.fail_test("get_occupation_skills", "No occupation skills returned")
                except Exception as e:
                    result.fail_test("get_occupation_skills", str(e))

                # Test get similar occupations
                try:
                    similar_occs = await client.get_similar_occupations("15-1252.00", limit=5)
                    if similar_occs and len(similar_occs) > 0:
                        result.pass_test(f"get_similar_occupations - Found {len(similar_occs)} similar occupations")
                    else:
                        result.fail_test("get_similar_occupations", "No similar occupations returned")
                except Exception as e:
                    result.fail_test("get_similar_occupations", str(e))

                # Test get similar skills
                try:
                    similar_skills = await client.get_similar_skills("KS1200364C9C1LK3V5Q1", limit=5)  # Python skill ID
                    if similar_skills and len(similar_skills) > 0:
                        result.pass_test(f"get_similar_skills - Found {len(similar_skills)} similar skills")
                    else:
                        result.fail_test("get_similar_skills", "No similar skills returned")
                except Exception as e:
                    result.fail_test("get_similar_skills", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_occupation_benchmark_api(self) -> APITestResult:
        """Test Occupation Benchmark API endpoints."""
        result = APITestResult("Occupation Benchmark API")
        client = OccupationBenchmarkAPIClient()
        
        try:
            async with client:
                # Test get benchmark data
                try:
                    benchmark = await client.get_benchmark_data(
                        occupation_id="15-1252.00",  # Software Developers
                        region="US",
                        metrics=["median_salary", "employment"]
                    )
                    if benchmark:
                        result.pass_test("get_benchmark_data - Got benchmark data")
                    else:
                        result.fail_test("get_benchmark_data", "No benchmark data returned")
                except Exception as e:
                    result.fail_test("get_benchmark_data", str(e))

                # Test get available areas
                try:
                    areas = await client.get_available_areas()
                    if areas and len(areas) > 0:
                        result.pass_test(f"get_available_areas - Found {len(areas)} areas")
                    else:
                        result.fail_test("get_available_areas", "No areas returned")
                except Exception as e:
                    result.fail_test("get_available_areas", str(e))

                # Test get available metrics
                try:
                    metrics = await client.get_available_metrics()
                    if metrics and len(metrics) > 0:
                        result.pass_test(f"get_available_metrics - Found {len(metrics)} metrics")
                    else:
                        result.fail_test("get_available_metrics", "No metrics returned")
                except Exception as e:
                    result.fail_test("get_available_metrics", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_career_pathways_api(self) -> APITestResult:
        """Test Career Pathways API endpoints."""
        result = APITestResult("Career Pathways API")
        client = CareerPathwaysAPIClient()
        
        try:
            async with client:
                # Test get available dimensions
                try:
                    dimensions = await client.get_available_dimensions()
                    if dimensions and len(dimensions) > 0:
                        result.pass_test(f"get_available_dimensions - Found {len(dimensions)} dimensions")
                    else:
                        result.fail_test("get_available_dimensions", "No dimensions returned")
                except Exception as e:
                    result.fail_test("get_available_dimensions", str(e))

                # Test get pathway analysis
                try:
                    pathway = await client.get_pathway_analysis(
                        from_occupation_id="15-1252.00",  # Software Developers
                        to_occupation_id="15-1253.00",    # Software QA Analysts
                    )
                    if pathway:
                        result.pass_test("get_pathway_analysis - Got pathway analysis")
                    else:
                        result.fail_test("get_pathway_analysis", "No pathway analysis returned")
                except Exception as e:
                    result.fail_test("get_pathway_analysis", str(e))

                # Test get API metadata
                try:
                    metadata = await client.get_api_metadata()
                    if metadata:
                        result.pass_test("get_api_metadata - Got metadata")
                    else:
                        result.fail_test("get_api_metadata", "No metadata returned")
                except Exception as e:
                    result.fail_test("get_api_metadata", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_job_postings_api(self) -> APITestResult:
        """Test Job Postings API endpoints."""
        result = APITestResult("Job Postings API")
        client = JobPostingsAPIClient()
        
        try:
            async with client:
                # Test get postings summary
                try:
                    summary = await client.get_postings_summary(
                        occupation_ids=["15-1252.00"],
                        location="US"
                    )
                    if summary:
                        result.pass_test("get_postings_summary - Got summary")
                    else:
                        result.fail_test("get_postings_summary", "No summary returned")
                except Exception as e:
                    result.fail_test("get_postings_summary", str(e))

                # Test get top skills
                try:
                    top_skills = await client.get_top_skills(
                        occupation_ids=["15-1252.00"],
                        limit=10
                    )
                    if top_skills and len(top_skills) > 0:
                        result.pass_test(f"get_top_skills - Found {len(top_skills)} skills")
                    else:
                        result.fail_test("get_top_skills", "No top skills returned")
                except Exception as e:
                    result.fail_test("get_top_skills", str(e))

                # Test get available facets
                try:
                    facets = await client.get_available_facets()
                    if facets and len(facets) > 0:
                        result.pass_test(f"get_available_facets - Found {len(facets)} facets")
                    else:
                        result.fail_test("get_available_facets", "No facets returned")
                except Exception as e:
                    result.fail_test("get_available_facets", str(e))

        except Exception as e:
            result.fail_test("API setup", str(e))
            
        return result

    async def test_workflow_integration(self) -> APITestResult:
        """Test the complete workflow integration."""
        result = APITestResult("Workflow Integration")
        
        try:
            async with TitleNormalizationWorkflow() as workflow:
                # Test complete workflow
                try:
                    workflow_result = await workflow.normalize_title_and_get_skills(
                        "senior software engineer",
                        max_occupations=3,
                        max_skills_per_occupation=10
                    )
                    if workflow_result.skills and len(workflow_result.skills) > 0:
                        result.pass_test(f"normalize_title_and_get_skills - Found {len(workflow_result.skills)} skills")
                    else:
                        result.fail_test("normalize_title_and_get_skills", "No skills returned")
                        
                    # Check workflow metadata
                    if "workflow_complete" in workflow_result.workflow_metadata["steps_completed"]:
                        result.pass_test("workflow_metadata - Workflow completed successfully")
                    else:
                        result.fail_test("workflow_metadata", "Workflow not marked as complete")
                        
                except Exception as e:
                    result.fail_test("normalize_title_and_get_skills", str(e))

                # Test simplified workflow
                try:
                    simple_result = await workflow.get_title_skills_simple(
                        "data scientist",
                        limit=15
                    )
                    if simple_result["skills"] and len(simple_result["skills"]) > 0:
                        result.pass_test(f"get_title_skills_simple - Found {len(simple_result['skills'])} skills")
                    else:
                        result.pass_test("get_title_skills_simple - No skills but no error")
                except Exception as e:
                    result.fail_test("get_title_skills_simple", str(e))

        except Exception as e:
            result.fail_test("Workflow setup", str(e))
            
        return result

    async def run_all_tests(self):
        """Run all API tests."""
        print("🚀 MCP Lightcast API Integration Tests")
        print("=" * 50)
        
        if not self.check_credentials():
            return False

        # Run all API tests
        test_methods = [
            self.test_skills_api,
            self.test_titles_api,
            self.test_classification_api,
            self.test_similarity_api,
            self.test_occupation_benchmark_api,
            self.test_career_pathways_api,
            self.test_job_postings_api,
            self.test_workflow_integration
        ]
        
        total_passed = 0
        total_failed = 0
        
        for test_method in test_methods:
            print(f"\n🧪 Testing {test_method.__name__.replace('test_', '').replace('_', ' ').title()}...")
            try:
                result = await test_method()
                result.summary()
                total_passed += result.passed
                total_failed += result.failed
            except Exception as e:
                print(f"❌ Failed to run {test_method.__name__}: {e}")
                total_failed += 1

        # Overall summary
        print("\n" + "=" * 50)
        print(f"📊 OVERALL RESULTS: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 All API tests passed!")
            return True
        else:
            print(f"⚠️  {total_failed} tests failed - check API credentials and network connectivity")
            return False


async def main():
    """Main entry point for manual API tests."""
    tester = ManualAPITester()
    success = await tester.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())