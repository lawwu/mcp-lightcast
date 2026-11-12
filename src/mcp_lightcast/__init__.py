"""MCP server for Lightcast API integration."""

import asyncio
import logging
from importlib.metadata import version
from pathlib import Path
from typing import Literal

import click
from dotenv import load_dotenv


@click.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to a .env file.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"]),
    default="stdio",
    show_default=True,
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Suppress logging and the server banner."
)
@click.option(
    "--host", default="127.0.0.1", show_default=True, help="HTTP bind address."
)
@click.option("--port", type=click.IntRange(1, 65535), default=3000, show_default=True)
@click.option(
    "--validate-config",
    is_flag=True,
    help="Verify credentials with Lightcast, then exit.",
)
@click.version_option(version=version("mcp-lightcast"))
def main(
    env_file: Path | None,
    transport: Literal["stdio", "streamable-http"],
    log_level: str,
    quiet: bool,
    host: str,
    port: int,
    validate_config: bool,
) -> None:
    """Connect MCP clients to Lightcast's labor-market APIs."""
    # Load before importing clients or constructing configuration, including in wheels.
    load_dotenv(env_file or Path.cwd() / ".env", override=False)
    from .settings import get_settings

    get_settings.cache_clear()
    config = get_settings()
    logging.basicConfig(
        level=logging.CRITICAL if quiet else getattr(logging, log_level),
        format="%(levelname)s %(name)s: %(message)s",
    )
    # HTTP request logging can expose query text; keep it off by default.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if config.credential_mode == "headers" and (
        transport != "streamable-http" or validate_config
    ):
        raise click.ClickException(
            "Header credentials require --transport streamable-http and cannot use "
            "--validate-config; credentials are supplied on each HTTP request."
        )
    if config.credential_mode == "environment" and (
        not config.client_id or not config.client_secret
    ):
        raise click.ClickException(
            "Set LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET (or use --env-file)."
        )
    if validate_config:
        from .auth.oauth import AuthenticationError, LightcastAuth

        try:
            asyncio.run(LightcastAuth(config).get_access_token())
        except AuthenticationError as exc:
            raise click.ClickException(str(exc)) from None
        click.echo("Configuration and authentication verified.", err=True)
        return
    from .server import mcp

    kwargs = (
        {"host": host, "port": port, "host_origin_protection": True}
        if transport == "streamable-http"
        else {}
    )
    mcp.run(transport=transport, show_banner=not quiet, **kwargs)
