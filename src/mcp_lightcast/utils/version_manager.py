"""Latest versions discovered from service metadata, with a one-hour cache."""

import time
from weakref import WeakKeyDictionary

from ..apis.base import (
    APIError,
    BaseLightcastClient,
    RequestRuntime,
    get_request_runtime,
)


class VersionManager:
    def __init__(self) -> None:
        self._caches: WeakKeyDictionary[
            RequestRuntime, dict[tuple[str, str, str, str], tuple[str, float]]
        ] = WeakKeyDictionary()

    async def _latest(self, api: str) -> str:
        runtime = get_request_runtime()
        config = runtime.config
        credentials = await runtime.credentials()
        cache = self._caches.setdefault(runtime, {})
        key = (
            api,
            config.base_url,
            config.api_scopes.get(api, config.oauth_scope),
            credentials.identity(config.oauth_url),
        )
        version, expires = cache.get(key, ("", 0))
        if time.monotonic() < expires:
            return version
        async with BaseLightcastClient(api) as client:
            version = (await client.get("meta")).get("data", {}).get("latestVersion")
        if not isinstance(version, str) or not version:
            raise APIError(f"No latest version in {api} metadata.")
        cache[key] = (version, time.monotonic() + 3600)
        if len(cache) > 256:
            cache.pop(next(iter(cache)))
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
