#!/usr/bin/env python3
"""
Authentication debugging script for Lightcast API.
Helps diagnose 401 errors and OAuth configuration issues.
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime
import httpx

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.mcp_lightcast.auth.oauth import lightcast_auth, AuthenticationError


async def debug_authentication():
    """Debug authentication step by step."""
    print("🔍 Lightcast API Authentication Debugging")
    print("=" * 60)
    
    results = []
    
    # Step 1: Check configuration
    print("\n🔧 Step 1: Checking Configuration...")
    try:
        print(f"   Client ID: {lightcast_auth.client_id[:10]}..." if lightcast_auth.client_id else "   Client ID: NOT SET")
        print(f"   Client Secret: {'*' * len(lightcast_auth.client_secret) if lightcast_auth.client_secret else 'NOT SET'}")
        print(f"   OAuth URL: {lightcast_auth.oauth_url}")
        print(f"   Default Scope: {lightcast_auth.oauth_scope}")
        print(f"   Dynamic Scope: {getattr(lightcast_auth, '_scope', 'None')}")
        
        config_ok = bool(lightcast_auth.client_id and lightcast_auth.client_secret)
        print(f"   Configuration: {'✅ OK' if config_ok else '❌ MISSING CREDENTIALS'}")
        
        results.append({
            "step": "Configuration Check",
            "status": "SUCCESS" if config_ok else "FAILED",
            "details": {
                "has_client_id": bool(lightcast_auth.client_id),
                "has_client_secret": bool(lightcast_auth.client_secret),
                "oauth_url": lightcast_auth.oauth_url,
                "default_scope": lightcast_auth.oauth_scope
            }
        })
        
    except Exception as e:
        print(f"   ❌ Configuration Error: {e}")
        results.append({
            "step": "Configuration Check",
            "status": "ERROR",
            "error": str(e)
        })
    
    # Step 2: Test OAuth endpoint connectivity
    print("\n🌐 Step 2: Testing OAuth Endpoint Connectivity...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                lightcast_auth.oauth_url,
                timeout=10.0
            )
            print(f"   OAuth Endpoint Response: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            connectivity_ok = response.status_code in [200, 405, 404]  # 405 is OK for GET on POST endpoint
            print(f"   Connectivity: {'✅ OK' if connectivity_ok else '❌ FAILED'}")
            
            results.append({
                "step": "OAuth Connectivity",
                "status": "SUCCESS" if connectivity_ok else "FAILED",
                "details": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            })
            
    except Exception as e:
        print(f"   ❌ Connectivity Error: {e}")
        results.append({
            "step": "OAuth Connectivity",
            "status": "ERROR",
            "error": str(e)
        })
    
    # Step 3: Test token acquisition with default scope
    print("\n🎫 Step 3: Testing Token Acquisition (Default Scope)...")
    try:
        # Clear any existing token to force refresh
        lightcast_auth._token = None
        lightcast_auth._scope = None
        
        token = await lightcast_auth.get_access_token()
        print(f"   Token acquired: {token[:20]}...")
        print(f"   Token length: {len(token)}")
        print(f"   Current scope used: {lightcast_auth._current_scope}")
        print(f"   Token expires at: {datetime.fromtimestamp(lightcast_auth._token_expires_at)}")
        
        default_token_ok = bool(token and len(token) > 20)
        print(f"   Default Token: {'✅ OK' if default_token_ok else '❌ FAILED'}")
        
        results.append({
            "step": "Default Token Acquisition",
            "status": "SUCCESS" if default_token_ok else "FAILED",
            "details": {
                "token_length": len(token) if token else 0,
                "scope_used": lightcast_auth._current_scope,
                "expires_at": lightcast_auth._token_expires_at
            }
        })
        
    except Exception as e:
        print(f"   ❌ Token Error: {e}")
        results.append({
            "step": "Default Token Acquisition",
            "status": "ERROR",
            "error": str(e)
        })
    
    # Step 4: Test premium scope tokens
    print("\n🔐 Step 4: Testing Premium Scope Tokens...")
    premium_scopes = [
        "classification_api",
        "similarity_api",
        "occupation_benchmark_api",
        "career_pathways_api",
        "job_postings_api"
    ]
    
    for scope in premium_scopes:
        try:
            print(f"\n   Testing scope: {scope}")
            
            # Set the premium scope
            lightcast_auth._scope = scope
            lightcast_auth._token = None  # Force token refresh
            
            token = await lightcast_auth.get_access_token()
            print(f"     Token acquired: {token[:20]}...")
            print(f"     Current scope: {lightcast_auth._current_scope}")
            
            scope_token_ok = bool(token and lightcast_auth._current_scope == scope)
            print(f"     Status: {'✅ OK' if scope_token_ok else '❌ FAILED'}")
            
            results.append({
                "step": f"Premium Token ({scope})",
                "status": "SUCCESS" if scope_token_ok else "FAILED",
                "details": {
                    "scope_requested": scope,
                    "scope_received": lightcast_auth._current_scope,
                    "token_length": len(token) if token else 0
                }
            })
            
        except Exception as e:
            print(f"     ❌ Error: {e}")
            results.append({
                "step": f"Premium Token ({scope})",
                "status": "ERROR",
                "error": str(e)
            })
    
    # Step 5: Test actual API call
    print("\n🚀 Step 5: Testing Actual API Call...")
    try:
        # Reset to default scope for basic API test
        lightcast_auth._scope = None
        lightcast_auth._token = None
        
        headers = await lightcast_auth.get_auth_headers()
        
        async with httpx.AsyncClient() as client:
            # Test with a basic endpoint that should work with emsi_open scope
            response = await client.get(
                "https://api.lightcast.io/titles/versions/latest",
                headers=headers,
                timeout=30.0
            )
            
            print(f"   API Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   API Data Sample: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"   API Error: {response.text}")
            
            api_ok = response.status_code == 200
            print(f"   API Call: {'✅ OK' if api_ok else '❌ FAILED'}")
            
            results.append({
                "step": "Basic API Call",
                "status": "SUCCESS" if api_ok else "FAILED",
                "details": {
                    "status_code": response.status_code,
                    "response_preview": response.text[:200] if response.text else None
                }
            })
            
    except Exception as e:
        print(f"   ❌ API Call Error: {e}")
        results.append({
            "step": "Basic API Call",
            "status": "ERROR",
            "error": str(e)
        })
    
    # Write results to file
    results_file = "auth_debug_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_steps": len(results),
                "successful_steps": sum(1 for r in results if r["status"] == "SUCCESS"),
                "failed_steps": sum(1 for r in results if r["status"] == "FAILED"),
                "error_steps": sum(1 for r in results if r["status"] == "ERROR")
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results written to: {results_file}")
    
    # Summary
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    total = len(results)
    print(f"\n📊 Summary: {successful}/{total} steps successful")
    
    # Provide specific recommendations
    print(f"\n💡 Recommendations:")
    
    config_failed = any(r for r in results if "Configuration" in r["step"] and r["status"] != "SUCCESS")
    if config_failed:
        print("   1. ❌ Fix your .env file with valid LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET")
    else:
        print("   1. ✅ Configuration looks good")
    
    connectivity_failed = any(r for r in results if "Connectivity" in r["step"] and r["status"] != "SUCCESS")
    if connectivity_failed:
        print("   2. ❌ Check internet connection and Lightcast service status")
    else:
        print("   2. ✅ OAuth endpoint is reachable")
    
    token_failed = any(r for r in results if "Token" in r["step"] and r["status"] == "ERROR")
    if token_failed:
        print("   3. ❌ Token acquisition failed - check credentials with Lightcast support")
    else:
        print("   3. ✅ Token acquisition working")
    
    premium_failed = any(r for r in results if "Premium Token" in r["step"] and r["status"] == "ERROR")
    if premium_failed:
        print("   4. ❌ Premium scopes not accessible - contact Lightcast to upgrade your plan")
    else:
        print("   4. ✅ Premium scope tokens working (if you have premium access)")
    
    api_failed = any(r for r in results if "API Call" in r["step"] and r["status"] != "SUCCESS")
    if api_failed:
        print("   5. ❌ API calls failing - may be related to scope or endpoint issues")
    else:
        print("   5. ✅ Basic API calls working")


if __name__ == "__main__":
    asyncio.run(debug_authentication())