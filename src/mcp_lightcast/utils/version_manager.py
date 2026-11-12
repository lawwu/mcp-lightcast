"""Latest versions discovered from service metadata, with a one-hour cache."""

import time

from ..apis.base import APIError, BaseLightcastClient


class VersionManager:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, float]] = {}

    async def _latest(self, api: str) -> str:
        version, expires = self._cache.get(api, ("", 0))
        if time.monotonic() < expires:
            return version
        async with BaseLightcastClient(api) as client:
            version = (await client.get("meta")).get("data", {}).get("latestVersion")
        if not isinstance(version, str) or not version:
            raise APIError(f"No latest version in {api} metadata.")
        self._cache[api] = (version, time.monotonic() + 3600)
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
