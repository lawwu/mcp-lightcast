"""MCP server registration; importing this module never authenticates."""

from datetime import UTC, datetime
from importlib.metadata import version

from fastmcp import FastMCP

from .settings import ServerConfig
from .tools.classification_tools import register_classification_tools
from .tools.job_postings_tools import register_job_postings_tools
from .tools.occupation_benchmark_tools import register_occupation_benchmark_tools
from .tools.similarity_tools import register_similarity_tools
from .tools.skills_tools import register_skills_tools
from .tools.titles_tools import register_titles_tools
from .tools.workflow_tools import register_workflow_tools

server_config = ServerConfig()
mcp = FastMCP(
    name=server_config.server_name, mask_error_details=server_config.mask_error_details
)
for register in (
    register_skills_tools,
    register_titles_tools,
    register_job_postings_tools,
    register_classification_tools,
    register_occupation_benchmark_tools,
    register_similarity_tools,
    register_workflow_tools,
):
    register(mcp)


@mcp.resource("lightcast://server/info")
async def server_info() -> dict:
    """Server version and supported API families; access depends on your subscription."""
    return {
        "name": server_config.server_name,
        "version": version("mcp-lightcast"),
        "supported_apis": [
            "Skills",
            "Titles",
            "Classification",
            "Similarity",
            "Occupation Benchmark",
            "Career Pathways",
            "US Job Postings",
        ],
        "documentation": "https://lawwu.github.io/mcp-lightcast/",
        "authentication": "OAuth2 client credentials",
    }


@mcp.resource("lightcast://server/health")
async def health_check() -> dict:
    """Check OAuth for the configured default scope; does not verify all premium APIs."""
    from .auth.oauth import AuthenticationError, lightcast_auth

    try:
        await lightcast_auth.get_access_token()
        return {
            "status": "healthy",
            "authentication": "verified",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except AuthenticationError as exc:
        return {
            "status": "unhealthy",
            "error": "Authentication failed"
            if server_config.mask_error_details
            else str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
        }
