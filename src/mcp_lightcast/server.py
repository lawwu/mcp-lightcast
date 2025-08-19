"""Main MCP server for Lightcast API integration."""

import asyncio
import logging
from fastmcp import FastMCP

from config.settings import server_config
from src.mcp_lightcast.tools.titles_tools import register_titles_tools
from src.mcp_lightcast.tools.skills_tools import register_skills_tools
from src.mcp_lightcast.tools.workflow_tools import register_workflow_tools


# Configure logging
logging.basicConfig(
    level=getattr(logging, server_config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP(
    name=server_config.server_name,
    mask_error_details=server_config.mask_error_details,
    dependencies=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0"
    ]
)

# Register error handler
@mcp.error_handler
async def handle_error(error: Exception) -> str:
    """Handle errors in MCP tools."""
    logger.error(f"MCP tool error: {str(error)}", exc_info=True)
    
    if server_config.mask_error_details:
        return "An error occurred while processing your request. Please check your parameters and try again."
    else:
        return f"Error: {str(error)}"

# Register all tool categories
register_titles_tools(mcp)
register_skills_tools(mcp)
register_workflow_tools(mcp)

# Add server metadata
@mcp.resource("server/info")
async def server_info() -> dict:
    """Get information about the Lightcast MCP server."""
    return {
        "name": server_config.server_name,
        "description": "MCP server providing access to Lightcast API for job titles, skills, and career data",
        "version": "0.1.0",
        "supported_apis": [
            "Titles API - Job title search, normalization, and hierarchy",
            "Skills API - Skills search, categorization, and extraction",
            "Classification API - Concept mapping to occupation codes",
            "Similarity API - Occupation and skill similarity analysis",
            "Workflow API - Combined title normalization and skills mapping"
        ],
        "authentication": "OAuth2 with client credentials",
        "rate_limits": "Configured per Lightcast API quotas"
    }

@mcp.resource("server/health")
async def health_check() -> dict:
    """Health check endpoint for the server."""
    try:
        # Test basic functionality
        from src.mcp_lightcast.auth.oauth import lightcast_auth
        
        # Try to get a token (this validates our auth configuration)
        token = await lightcast_auth.get_access_token()
        
        return {
            "status": "healthy",
            "authentication": "configured" if token else "failed",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e) if not server_config.mask_error_details else "Configuration error",
            "timestamp": asyncio.get_event_loop().time()
        }

if __name__ == "__main__":
    logger.info(f"Starting {server_config.server_name}")
    mcp.run()