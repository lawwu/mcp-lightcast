"""Discover and pin taxonomy versions for a reproducible lookup."""
import asyncio
from mcp_lightcast.apis.skills import SkillsAPIClient
from mcp_lightcast.apis.titles import TitlesAPIClient
from mcp_lightcast.utils.version_manager import version_manager


async def main():
    titles_version = await version_manager.get_latest_titles_version()
    skills_version = await version_manager.get_latest_skills_version()
    print(f"Titles {titles_version}; Skills {skills_version}")
    async with TitlesAPIClient() as titles, SkillsAPIClient() as skills:
        print(await titles.search_titles("Software Engineer", version=titles_version))
        print(await skills.search_skills("Python", version=skills_version))


if __name__ == "__main__":
    asyncio.run(main())
