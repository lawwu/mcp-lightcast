"""Main MCP server for Lightcast API integration."""

import asyncio
import logging
import sys
from pathlib import Path

from fastmcp import FastMCP

# Add the project root to the Python path so we can import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import server_config
except ImportError:
    # Fallback for when config module is not in the path
    from pydantic import ConfigDict, Field
    from pydantic_settings import BaseSettings

    class ServerConfig(BaseSettings):
        model_config = ConfigDict(extra="ignore")

        server_name: str = Field(default="lightcast-mcp-server", alias="MCP_SERVER_NAME")
        log_level: str = Field(default="INFO", alias="LOG_LEVEL")
        mask_error_details: bool = Field(default=True, alias="MASK_ERROR_DETAILS")

    server_config = ServerConfig()

from .tools.career_pathways_tools import register_career_pathways_tools
from .tools.classification_tools import register_classification_tools
from .tools.job_postings_tools import register_job_postings_tools
from .tools.occupation_benchmark_tools import register_occupation_benchmark_tools
from .tools.similarity_tools import register_similarity_tools
from .tools.skills_tools import register_skills_tools
from .tools.titles_tools import register_titles_tools
from .tools.unified_skills_tools import register_unified_skills_tools
from .tools.workflow_tools import register_workflow_tools

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

# Note: Error handling is built into FastMCP, no need for custom handler

# Register all tool categories
register_titles_tools(mcp)
register_skills_tools(mcp)
register_workflow_tools(mcp)
register_classification_tools(mcp)
register_similarity_tools(mcp)
register_occupation_benchmark_tools(mcp)
register_career_pathways_tools(mcp)
register_job_postings_tools(mcp)
register_unified_skills_tools(mcp)

# Add server metadata
@mcp.resource("lightcast://server/info")
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
            "Occupation Benchmark API - Salary and employment benchmarks",
            "Career Pathways API - Career pathway analysis and planning",
            "Job Postings API - Job market insights and skill demand",
            "Workflow API - Combined title normalization and skills mapping"
        ],
        "authentication": "OAuth2 with client credentials",
        "rate_limits": "Configured per Lightcast API quotas"
    }

@mcp.resource("lightcast://server/health")
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
