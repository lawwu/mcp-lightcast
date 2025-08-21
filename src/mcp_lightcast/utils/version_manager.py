"""Utility to manage and fetch latest API versions."""

import logging

from ..apis.base import BaseLightcastClient

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages API versions and provides latest version information."""

    def __init__(self):
        self._latest_titles_version: str | None = None
        self._latest_skills_version: str | None = None
        self._cache_timeout = 3600  # 1 hour cache
        self._last_fetch_time = 0

    async def get_latest_titles_version(self) -> str:
        """Get the latest titles API version."""
        if self._latest_titles_version is None:
            await self._fetch_latest_versions()
        return self._latest_titles_version or "5.47"  # Fallback to known working version

    async def get_latest_skills_version(self) -> str:
        """Get the latest skills API version."""
        if self._latest_skills_version is None:
            await self._fetch_latest_versions()
        return self._latest_skills_version or "9.33"  # Fallback to known working version

    async def _fetch_latest_versions(self) -> None:
        """Fetch the latest API versions from Lightcast."""
        try:
            async with BaseLightcastClient() as client:
                # Fetch titles versions
                try:
                    titles_response = await client.get("titles/versions")
                    titles_versions = titles_response.get("data", [])
                    if titles_versions:
                        self._latest_titles_version = titles_versions[0]  # First is latest
                        logger.debug(f"Latest titles version: {self._latest_titles_version}")
                except Exception as e:
                    logger.warning(f"Failed to fetch titles versions: {e}")

                # Fetch skills versions
                try:
                    skills_response = await client.get("skills/versions")
                    skills_versions = skills_response.get("data", [])
                    if skills_versions:
                        self._latest_skills_version = skills_versions[0]  # First is latest
                        logger.debug(f"Latest skills version: {self._latest_skills_version}")
                except Exception as e:
                    logger.warning(f"Failed to fetch skills versions: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch API versions: {e}")
            # Use fallback versions
            self._latest_titles_version = "5.47"
            self._latest_skills_version = "9.33"

    def get_default_titles_version(self) -> str:
        """Get default titles version (synchronous)."""
        return "latest"  # Use Lightcast's 'latest' keyword

    def get_default_skills_version(self) -> str:
        """Get default skills version (synchronous)."""
        return "latest"  # Use Lightcast's 'latest' keyword


# Global version manager instance
version_manager = VersionManager()
