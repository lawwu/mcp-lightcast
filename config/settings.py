"""Configuration settings for MCP Lightcast server."""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field


class LightcastConfig(BaseSettings):
    """Configuration for Lightcast API."""
    
    client_id: str = Field(default="", env="LIGHTCAST_CLIENT_ID")
    client_secret: str = Field(default="", env="LIGHTCAST_CLIENT_SECRET")
    base_url: str = Field(default="https://api.lightcast.io", env="LIGHTCAST_BASE_URL")
    oauth_url: str = Field(default="https://auth.lightcast.io/oauth/token", env="LIGHTCAST_OAUTH_URL")
    rate_limit_per_hour: int = Field(default=1000, env="LIGHTCAST_RATE_LIMIT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ServerConfig(BaseSettings):
    """Configuration for MCP server."""
    
    server_name: str = Field(default="lightcast-mcp-server", env="MCP_SERVER_NAME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    mask_error_details: bool = Field(default=True, env="MASK_ERROR_DETAILS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instances
lightcast_config = LightcastConfig()
server_config = ServerConfig()