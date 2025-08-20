#!/usr/bin/env python3
"""Examples of how to use different API versions."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_lightcast.apis.titles import TitlesAPIClient
from src.mcp_lightcast.apis.skills import SkillsAPIClient

async def version_usage_examples():
    """Show different ways to use API versions."""
    
    print("🔧 Lightcast API Version Usage Examples")
    print("=" * 50)
    
    # Example 1: Use latest version (default)
    print("\n1️⃣ Using default 'latest' version:")
    async with TitlesAPIClient() as client:
        results = await client.search_titles("software engineer", limit=3)
        print(f"   Found {len(results)} titles using latest API version")
        
    # Example 2: Specify exact version
    print("\n2️⃣ Using specific version (5.47):")
    async with TitlesAPIClient() as client:
        results = await client.search_titles("software engineer", limit=3, version="5.47")
        print(f"   Found {len(results)} titles using API version 5.47")
        
    # Example 3: Use older version for consistency
    print("\n3️⃣ Using older version for consistency (5.46):")
    async with TitlesAPIClient() as client:
        results = await client.search_titles("software engineer", limit=3, version="5.46")
        print(f"   Found {len(results)} titles using API version 5.46")
        
    # Example 4: Skills API with different versions
    print("\n4️⃣ Skills API version examples:")
    async with SkillsAPIClient() as client:
        # Latest version
        latest_results = await client.search_skills("python", limit=2)
        print(f"   Latest: {len(latest_results)} skills")
        
        # Specific version
        specific_results = await client.search_skills("python", limit=2, version="9.33")
        print(f"   v9.33: {len(specific_results)} skills")
        
        # Older version
        older_results = await client.search_skills("python", limit=2, version="9.32")
        print(f"   v9.32: {len(older_results)} skills")
    
    print("\n✨ Benefits:")
    print("   • 'latest' always uses newest data and features")
    print("   • Specific versions ensure consistent results")
    print("   • Easy to test different API versions")
    print("   • Backward compatibility maintained")

if __name__ == "__main__":
    asyncio.run(version_usage_examples())