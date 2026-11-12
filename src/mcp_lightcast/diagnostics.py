"""Opt-in live MCP smoke checks. Never writes credentials or raw licensed data."""

import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastmcp import Client

from .server import mcp


async def run_checks(operations: bool = False) -> dict[str, Any]:
    logging.getLogger("fastmcp").setLevel(logging.CRITICAL)
    results: list[dict[str, Any]] = []
    async with Client(mcp) as client:

        async def check(name: str, args: dict | None = None) -> Any:
            try:
                result = await client.call_tool(name, args or {})
                value = result.structured_content
                if isinstance(value, dict) and set(value) == {"result"}:
                    value = value["result"]
                status = "passed"
                if (
                    isinstance(value, dict)
                    and value.get("workflow_metadata", {}).get("status") == "partial"
                ):
                    status = "partial"
                results.append({"tool": name, "status": status})
                print(f"{name}: {status}", flush=True)
                return value
            except Exception as exc:
                # Errors are already sanitized by the MCP boundary. Do not persist response bodies.
                results.append(
                    {"tool": name, "status": "failed", "error_type": type(exc).__name__}
                )
                print(f"{name}: failed ({type(exc).__name__})", flush=True)
                return None

        skills_meta = await check("get_skills_metadata")
        titles_meta = await check("get_titles_metadata")
        releases = await check("list_classification_releases")
        await check("get_classification_metadata")
        for tool in (
            "get_similarity_metadata",
            "get_benchmark_metadata",
            "get_pathways_metadata",
            "get_postings_metadata",
        ):
            await check(tool)
        if operations:
            skills = await check(
                "search_skills", {"query": "Python", "limit": 1, "skill_type": "ST1"}
            )
            titles = await check(
                "search_job_titles", {"query": "Software Engineer", "limit": 1}
            )
            if skills:
                sid = skills[0]["id"]
                for name, args in [
                    ("get_skill_details", {"skill_id": sid}),
                    ("bulk_retrieve_skills", {"skill_ids": [sid]}),
                    ("get_related_skills", {"skill_id": sid, "limit": 2}),
                    ("find_similar_skills", {"skill_id": sid, "limit": 2}),
                ]:
                    await check(name, args)
            if titles:
                tid = titles[0]["id"]
                await check("get_job_title_details", {"title_id": tid})
                await check("bulk_retrieve_titles", {"title_ids": [tid]})
            await check("normalize_job_title", {"title": "Software Engineer"})
            await check(
                "extract_skills_from_text",
                {"text": "Python programming and SQL databases."},
            )
            classified = await check(
                "classify_occupation", {"title": "Software Engineer", "limit": 1}
            )
            await check(
                "query_similarity", {"model": "soc", "input": "15-1252", "limit": 2}
            )
            await check(
                "get_occupation_benchmark",
                {"occupation_id": "231715", "metrics": ["taxonomicalInfo", "salary"]},
            )
            if classified and classified.get("data"):
                oid = classified["data"][0]["concept"]["id"]
                await check("get_career_next_steps", {"occupation_id": oid, "limit": 2})
            await check(
                "get_career_skill_gap",
                {
                    "source_id": "11-1021",
                    "destination_id": "11-1011",
                    "dimension": "soc",
                    "limit": 2,
                },
            )
            await check(
                "normalize_title_and_get_skills",
                {
                    "raw_title": "Software Engineer",
                    "max_occupations": 1,
                    "max_skills_per_occupation": 3,
                },
            )
            await check(
                "analyze_job_posting_skills",
                {
                    "job_title": "Python Developer",
                    "job_description": "Build software using Python and SQL.",
                },
            )
            await check(
                "normalize_title_and_extract_skills", {"title": "Python Developer"}
            )
            mappings = await check("list_taxonomy_mappings")
            if mappings:
                mapping = next(
                    (
                        m
                        for m in mappings
                        if m.get("sourceName") == "titles"
                        and m.get("destinationName") == "lot"
                    ),
                    None,
                )
                if mapping and titles:
                    await check(
                        "map_taxonomy_concepts",
                        {"mapping_name": mapping["name"], "ids": [titles[0]["id"]]},
                    )
            filters = {"when": "active", "title": ["ET6850661D6AE5FA86"]}
            await check("get_posting_statistics", {"filters": filters})
            await check(
                "get_posting_rankings",
                {"facet": "skills_name", "filters": filters, "limit": 2},
            )
            postings = await check(
                "search_job_postings", {"filters": filters, "limit": 1}
            )
            if postings and postings.get("data", {}).get("postings"):
                await check(
                    "get_job_posting_details",
                    {"posting_id": postings["data"]["postings"][0]["id"]},
                )
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "mode": "operations" if operations else "metadata",
        "versions": {
            "skills": (skills_meta or {}).get("version"),
            "titles": (titles_meta or {}).get("version"),
            "classification": releases[0]["release"] if releases else None,
        },
        "checks": results,
        "counts": {
            s: sum(r["status"] == s for r in results)
            for s in ("passed", "partial", "failed")
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operations",
        action="store_true",
        help="Also run data queries; consumes API/extraction/classification quotas.",
    )
    parser.add_argument("--output", type=Path, help="Write a sanitized JSON report.")
    args = parser.parse_args()
    report = asyncio.run(run_checks(args.operations))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["counts"]))
    raise SystemExit(
        1 if report["counts"]["failed"] or report["counts"]["partial"] else 0
    )


if __name__ == "__main__":
    main()
