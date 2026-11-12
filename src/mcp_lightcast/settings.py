"""Packaged, lazy configuration shared by the CLI and API clients."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LightcastConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    client_id: str = Field(default="", alias="LIGHTCAST_CLIENT_ID", repr=False)
    client_secret: str = Field(default="", alias="LIGHTCAST_CLIENT_SECRET", repr=False)
    base_url: str = Field(
        default="https://api.lightcast.io", alias="LIGHTCAST_BASE_URL"
    )
    classification_url: str = Field(
        default="https://classification.emsicloud.com",
        alias="LIGHTCAST_CLASSIFICATION_URL",
    )
    core_lmi_url: str = Field(
        default="https://agnitio.emsicloud.com", alias="LIGHTCAST_CORE_LMI_URL"
    )
    core_lmi_requests_per_second: float = Field(
        default=1, gt=0, alias="LIGHTCAST_CORE_LMI_REQUESTS_PER_SECOND"
    )
    oauth_url: str = Field(
        default="https://auth.emsicloud.com/connect/token", alias="LIGHTCAST_OAUTH_URL"
    )
    oauth_scope: str = Field(default="emsi_open", alias="LIGHTCAST_OAUTH_SCOPE")
    api_scopes: dict[str, str] = Field(
        default_factory=dict, alias="LIGHTCAST_API_SCOPES"
    )
    requests_per_second: float = Field(
        default=5, gt=0, alias="LIGHTCAST_REQUESTS_PER_SECOND"
    )
    timeout: float = Field(default=30, gt=0, alias="LIGHTCAST_TIMEOUT")
    max_retries: int = Field(default=2, ge=0, le=5, alias="LIGHTCAST_MAX_RETRIES")


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    server_name: str = Field(default="lightcast-mcp-server", alias="MCP_SERVER_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    mask_error_details: bool = Field(default=True, alias="MASK_ERROR_DETAILS")


@lru_cache
def get_settings() -> LightcastConfig:
    return LightcastConfig()
