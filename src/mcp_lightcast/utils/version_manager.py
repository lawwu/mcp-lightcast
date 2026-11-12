"""Latest versions discovered from service metadata, with a one-hour cache."""

import time

from ..apis.base import APIError, BaseLightcastClient
from ..auth.credentials import get_credentials
from ..settings import get_settings


class VersionManager:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str, str], tuple[str, float]] = {}

    async def _latest(self, api: str) -> str:
        config = get_settings()
        credentials = await get_credentials()
        key = (api, config.base_url, credentials.identity(config.oauth_url))
        version, expires = self._cache.get(key, ("", 0))
        if time.monotonic() < expires:
            return version
        async with BaseLightcastClient(api) as client:
            version = (await client.get("meta")).get("data", {}).get("latestVersion")
        if not isinstance(version, str) or not version:
            raise APIError(f"No latest version in {api} metadata.")
        self._cache[key] = (version, time.monotonic() + 3600)
        if len(self._cache) > 256:
            self._cache.pop(next(iter(self._cache)))
        return version

    async def get_latest_titles_version(self) -> str:
        return await self._latest("titles")

    async def get_latest_skills_version(self) -> str:
        return await self._latest("skills")

    def get_default_titles_version(self) -> str:
        return "latest"

    def get_default_skills_version(self) -> str:
        return "latest"


version_manager = VersionManager()
