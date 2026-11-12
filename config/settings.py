"""Compatibility imports; configuration now ships inside the installed package."""
from mcp_lightcast.settings import LightcastConfig, ServerConfig, get_settings

lightcast_config = get_settings()
server_config = ServerConfig()
