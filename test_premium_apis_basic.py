#!/usr/bin/env python3
"""
Basic test script for premium Lightcast API clients.
Tests client initialization and OAuth scope handling without requiring premium access.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.mcp_lightcast.apis.classification import ClassificationAPIClient
from src.mcp_lightcast.apis.similarity import SimilarityAPIClient
from src.mcp_lightcast.apis.occupation_benchmark import OccupationBenchmarkAPIClient
from src.mcp_lightcast.apis.career_pathways import CareerPathwaysAPIClient
from src.mcp_lightcast.apis.job_postings import JobPostingsAPIClient


async def test_basic_functionality():
    """Test basic client initialization and scope handling."""
    print("🔍 Testing Premium API Client Initialization...")
    print("=" * 60)
    
    results = []
    
    # Test each premium API client
    premium_apis = [
        ("Classification", ClassificationAPIClient, "classification_api"),
        ("Similarity", SimilarityAPIClient, "similarity_api"),
        ("Occupation Benchmark", OccupationBenchmarkAPIClient, "occupation_benchmark_api"),
        ("Career Pathways", CareerPathwaysAPIClient, "career_pathways_api"),
        ("Job Postings", JobPostingsAPIClient, "job_postings_api"),
    ]
    
    for api_name, client_class, expected_scope in premium_apis:
        try:
            print(f"\n🧪 Testing {api_name} API Client...")
            
            # Test client initialization
            client = client_class()
            
            # Check if the correct scope was set
            from src.mcp_lightcast.auth.oauth import lightcast_auth
            current_scope = getattr(lightcast_auth, '_scope', None)
            
            scope_correct = current_scope == expected_scope
            
            print(f"   ✅ Client initialized successfully")
            print(f"   ✅ Expected scope: {expected_scope}")
            print(f"   ✅ Current scope: {current_scope}")
            print(f"   {'✅' if scope_correct else '❌'} Scope correctly set: {scope_correct}")
            
            # Test async context manager
            async with client:
                print(f"   ✅ Async context manager works")
            
            results.append({
                "api": api_name,
                "initialization": True,
                "scope_handling": scope_correct,
                "async_context": True,
                "error": None
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                "api": api_name,
                "initialization": False,
                "scope_handling": False,
                "async_context": False,
                "error": str(e)
            })
    
    # Write results to file
    results_file = "premium_api_basic_test_results.txt"
    
    with open(results_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PREMIUM API BASIC FUNCTIONALITY TEST RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Type: Basic client initialization and scope handling\n")
        f.write("=" * 80 + "\n\n")
        
        total_apis = len(results)
        successful_inits = sum(1 for r in results if r["initialization"])
        successful_scopes = sum(1 for r in results if r["scope_handling"])
        
        f.write(f"SUMMARY:\n")
        f.write(f"Total APIs tested: {total_apis}\n")
        f.write(f"Successful initializations: {successful_inits}/{total_apis}\n")
        f.write(f"Correct scope handling: {successful_scopes}/{total_apis}\n")
        f.write(f"Overall success rate: {(successful_inits/total_apis*100):.1f}%\n\n")
        
        f.write("DETAILED RESULTS:\n")
        f.write("-" * 40 + "\n")
        
        for result in results:
            f.write(f"\n{result['api']} API:\n")
            f.write(f"  Initialization: {'SUCCESS' if result['initialization'] else 'FAILED'}\n")
            f.write(f"  Scope Handling: {'SUCCESS' if result['scope_handling'] else 'FAILED'}\n")
            f.write(f"  Async Context: {'SUCCESS' if result['async_context'] else 'FAILED'}\n")
            
            if result['error']:
                f.write(f"  Error: {result['error']}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF BASIC TEST RESULTS\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n📄 Basic test results written to: {results_file}")
    print(f"📊 Summary: {successful_inits}/{total_apis} clients initialized successfully")
    print(f"🎯 Scope handling: {successful_scopes}/{total_apis} correct")
    
    # Show next steps
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. Check your .env file has the required credentials:")
    print(f"      - LIGHTCAST_CLIENT_ID")
    print(f"      - LIGHTCAST_CLIENT_SECRET")
    print(f"   2. Ensure you have premium API access for full testing")
    print(f"   3. Run the full test: python test_premium_apis.py")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())