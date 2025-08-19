#!/usr/bin/env python3
"""
Simple runner script for the MCP Lightcast server.

This script provides an easy way to start the server with proper error handling
and configuration validation.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = [
        "LIGHTCAST_CLIENT_ID",
        "LIGHTCAST_CLIENT_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        print("See .env.example for the complete list of configuration options.")
        return False
    
    return True

def load_dotenv_if_available():
    """Load .env file if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
        else:
            print(f"⚠️  No .env file found at {env_file}")
            print("   You can copy .env.example to .env and configure your settings.")
    except ImportError:
        print("⚠️  python-dotenv not available, skipping .env file loading")

async def test_authentication():
    """Test that authentication is working properly."""
    try:
        from src.mcp_lightcast.auth.oauth import lightcast_auth
        token = await lightcast_auth.get_access_token()
        if token:
            print("✅ Authentication successful")
            return True
        else:
            print("❌ Authentication failed - no token received")
            return False
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return False

async def main():
    """Main entry point."""
    print("🚀 Starting MCP Lightcast Server")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv_if_available()
    
    # Validate configuration
    if not validate_environment():
        sys.exit(1)
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    if not await test_authentication():
        print("\n💡 Make sure your Lightcast API credentials are correct.")
        print("   Contact Lightcast if you need API access: https://docs.lightcast.dev/contact")
        sys.exit(1)
    
    # Start the server
    print("\n🎯 Starting MCP server...")
    print("   Use Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        from src.mcp_lightcast.server import mcp
        mcp.run()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server error: {str(e)}")
        logging.exception("Server startup failed")
        sys.exit(1)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Startup error: {str(e)}")
        sys.exit(1)