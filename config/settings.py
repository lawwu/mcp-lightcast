"""Configuration settings for MCP Lightcast server."""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, ConfigDict
except ImportError:
    from pydantic import BaseSettings, Field, ConfigDict


class LightcastConfig(BaseSettings):
    """Configuration for Lightcast API."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra environment variables
    )
    
    client_id: str = Field(default="", alias="LIGHTCAST_CLIENT_ID")
    client_secret: str = Field(default="", alias="LIGHTCAST_CLIENT_SECRET")
    base_url: str = Field(default="https://api.lightcast.io", alias="LIGHTCAST_BASE_URL")
    oauth_url: str = Field(default="https://auth.emsicloud.com/connect/token", alias="LIGHTCAST_OAUTH_URL")
    oauth_scope: str = Field(default="emsi_open", alias="LIGHTCAST_OAUTH_SCOPE")
    rate_limit_per_hour: int = Field(default=1000, alias="LIGHTCAST_RATE_LIMIT")


class ServerConfig(BaseSettings):
    """Configuration for MCP server."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra environment variables
    )
    
    server_name: str = Field(default="lightcast-mcp-server", alias="MCP_SERVER_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    mask_error_details: bool = Field(default=True, alias="MASK_ERROR_DETAILS")


# Global configuration instances
lightcast_config = LightcastConfig()
server_config = ServerConfig()