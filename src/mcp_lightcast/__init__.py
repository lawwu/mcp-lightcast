"""MCP server for Lightcast API integration."""

import asyncio
import logging
import os
from pathlib import Path

import click
from dotenv import load_dotenv

# Remove direct import to avoid circular dependency
from .auth.oauth import lightcast_auth


def setup_logging(level: str, quiet: bool = False):
    """Set up logging configuration."""
    if quiet:
        logging.disable(logging.CRITICAL)
        return

    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to environment file (.env)",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"], case_sensitive=False),
    default="streamable-http",
    help="Transport method for MCP communication (default: streamable-http)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set logging level (default: INFO)",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress all logging output",
)
@click.option(
    "--port",
    type=int,
    default=3000,
    help="Port for HTTP transport (default: 3000)",
)
@click.option(
    "--validate-config",
    is_flag=True,
    help="Validate configuration and exit",
)
@click.version_option(version=None, prog_name="mcp-lightcast")
def main(
    env_file: Path | None = None,
    transport: str = "streamable-http",
    log_level: str = "INFO",
    quiet: bool = False,
    port: int = 3000,
    validate_config: bool = False,
):
    """
    MCP server for Lightcast API integration.

    Provides tools for job titles, skills analysis, and career data through
    the Model Context Protocol (MCP).
    """
    # Load environment variables
    if env_file and env_file.exists():
        load_dotenv(env_file)
        if not quiet:
            click.echo(f"✅ Loaded environment from {env_file}")
    elif os.path.exists(".env"):
        load_dotenv()
        if not quiet:
            click.echo("✅ Loaded environment from .env")
    # Set up logging
    setup_logging(log_level, quiet)
    logger = logging.getLogger(__name__)
    # Validate configuration
    import sys
    from pathlib import Path
    # Add project root to path for config import
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    try:
        from config.settings import lightcast_config
    except ImportError:
        # Fallback configuration
        from pydantic import ConfigDict, Field
        from pydantic_settings import BaseSettings
        class LightcastConfig(BaseSettings):
            model_config = ConfigDict(extra="ignore")
            client_id: str = Field(default="", alias="LIGHTCAST_CLIENT_ID")
            client_secret: str = Field(default="", alias="LIGHTCAST_CLIENT_SECRET")
            base_url: str = Field(default="https://api.lightcast.io", alias="LIGHTCAST_BASE_URL")
            oauth_url: str = Field(default="https://auth.emsicloud.com/connect/token", alias="LIGHTCAST_OAUTH_URL")
            oauth_scope: str = Field(default="emsi_open", alias="LIGHTCAST_OAUTH_SCOPE")
            rate_limit_per_hour: int = Field(default=1000, alias="LIGHTCAST_RATE_LIMIT")
        lightcast_config = LightcastConfig()

    if not lightcast_config.client_id or not lightcast_config.client_secret:
        click.echo("❌ Error: Missing required environment variables:", err=True)
        click.echo("   - LIGHTCAST_CLIENT_ID", err=True)
        click.echo("   - LIGHTCAST_CLIENT_SECRET", err=True)
        click.echo("\nPlease set these variables in your .env file or environment.", err=True)
        click.echo("See .env.example for the complete list of configuration options.", err=True)
        raise click.ClickException("Missing required configuration")

    if validate_config:
        # Test authentication
        async def test_auth():
            try:
                token = await lightcast_auth.get_access_token()
                return bool(token)
            except Exception as e:
                click.echo(f"❌ Authentication failed: {e}", err=True)
                return False

        if asyncio.run(test_auth()):
            click.echo("✅ Configuration is valid")
            click.echo("✅ Authentication successful")
            return
        else:
            raise click.ClickException("Configuration validation failed")

    if not quiet:
        click.echo("🚀 Starting MCP Lightcast Server")
        click.echo(f"   Transport: {transport}")
        if transport.lower() == "streamable-http":
            click.echo(f"   Port: {port}")
        click.echo(f"   Log Level: {log_level}")
        click.echo(f"   Base URL: {lightcast_config.base_url}")
        click.echo("=" * 50)

    try:
        # Test authentication on startup
        async def startup_check():
            try:
                await lightcast_auth.get_access_token()
                if not quiet:
                    logger.info("✅ Authentication successful")
                return True
            except Exception as e:
                logger.error(f"❌ Authentication failed: {e}")
                return False

        if not asyncio.run(startup_check()):
            raise click.ClickException("Authentication failed on startup")

        # Start the server based on transport
        if transport.lower() == "stdio":
            # Import here to avoid circular dependency
            from .server import mcp as server_instance
            server_instance.run()
        elif transport.lower() == "streamable-http":
            # Import here to avoid circular dependency
            from .server import mcp as server_instance
            server_instance.run(transport="streamable-http", port=port)
        else:
            raise click.ClickException(f"Transport '{transport}' not yet implemented")

    except KeyboardInterrupt:
        if not quiet:
            click.echo("\n👋 Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        raise click.ClickException(f"Server startup failed: {e}") from e


if __name__ == "__main__":
    main()
