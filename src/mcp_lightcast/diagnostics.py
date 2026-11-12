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


async def run_core_lmi_checks() -> dict[str, Any]:
    """Exercise discovery and small data queries without persisting market data."""
    logging.getLogger("fastmcp").setLevel(logging.CRITICAL)
    checks: list[dict[str, Any]] = []
    versions: dict[str, str] = {}
    async with Client(mcp) as client:

        async def check(
            label: str, tool: str, args: dict[str, Any], data_query: bool = False
        ) -> Any:
            try:
                value = (await client.call_tool(tool, args)).structured_content
                if data_query and (not value or value["pagination"]["returned"] < 1):
                    raise ValueError("Expected a nonempty data page")
                entry = {"check": label, "tool": tool, "status": "passed"}
                checks.append(entry)
                print(f"{label}: passed", flush=True)
                return value
            except Exception as exc:
                checks.append(
                    {
                        "check": label,
                        "tool": tool,
                        "status": "failed",
                        "error_type": type(exc).__name__,
                    }
                )
                print(f"{label}: failed ({type(exc).__name__})", flush=True)
                return None

        catalog = await check(
            "accessible datasets", "list_core_lmi_datasets", {"limit": 100}
        )
        await check(
            "dataset definitions",
            "list_core_lmi_datasets",
            {"query": "occupation", "include_definitions": True, "limit": 2},
        )
        metadata: dict[str, Any] = {}
        for family in ("occupation", "industry", "completers"):
            dataset = "emsi.us." + family
            releases = await check(
                f"{family} releases", "get_core_lmi_versions", {"dataset": dataset}
            )
            if not releases or not releases["latest_numeric"]:
                continue
            versions[dataset] = releases["latest_numeric"]
            metadata[family] = await check(
                f"{family} metadata",
                "get_core_lmi_metadata",
                {"dataset": dataset, "version": versions[dataset], "limit": 1},
            )
        for family, dimension, search in (
            ("occupation", "Occupation", "Software Developers"),
            ("industry", "Industry", "Restaurants"),
            ("completers", "Program", "Computer Science"),
        ):
            dataset = "emsi.us." + family
            if dataset in versions:
                await check(
                    f"{family} dimension search",
                    "get_core_lmi_dimension",
                    {
                        "dataset": dataset,
                        "version": versions[dataset],
                        "dimension": dimension,
                        "search": search,
                        "limit": 5,
                    },
                )
        if "emsi.us.occupation" in versions:
            await check(
                "area hierarchy",
                "get_core_lmi_dimension",
                {
                    "dataset": "emsi.us.occupation",
                    "version": versions["emsi.us.occupation"],
                    "dimension": "Area",
                    "level": "2",
                    "aggregation_path": "1",
                    "limit": 5,
                },
            )

        def mapping(dimension: str, groups: dict[str, list[str]]) -> dict[str, Any]:
            return {"dimensionName": dimension, "map": groups}

        employees = mapping("ClassOfWorker", {"Employees": ["1", "2"]})

        async def query(label: str, family: str, body: dict[str, Any]) -> Any:
            dataset = "emsi.us." + family
            if dataset not in versions:
                return None
            return await check(
                label,
                "query_core_lmi",
                {"dataset": dataset, "version": versions[dataset], "query": body},
                data_query=True,
            )

        if metadata.get("occupation"):
            year = metadata["occupation"]["attributes"]["currentYear"]
            body = {
                "metrics": [
                    {"name": f"Jobs.{year}"},
                    {"name": f"Jobs.{int(year) + 5}"},
                    {"name": "Earnings.Median.Annual"},
                ],
                "constraints": [
                    mapping("Area", {"California": ["6"], "Washington": ["53"]}),
                    mapping("Occupation", {"Software Developers": ["15-1252"]}),
                    employees,
                ],
                "sortBy": [{"name": "Area", "direction": "ascending"}],
                "limit": 1,
            }
            first = await query("employment and earnings page 1", "occupation", body)
            second = await query(
                "employment and earnings page 2", "occupation", {**body, "offset": 1}
            )
            distinct = bool(
                first
                and second
                and first["data"][0]["rows"] != second["data"][0]["rows"]
                and second["pagination"]["next_offset"] is None
            )
            checks.append(
                {
                    "check": "distinct complete query pages",
                    "tool": "query_core_lmi",
                    "status": "passed" if distinct else "failed",
                }
            )
        if metadata.get("industry"):
            year = metadata["industry"]["attributes"]["currentYear"]
            await query(
                "regional restaurant employment",
                "industry",
                {
                    "metrics": [
                        {"name": f"Jobs.{year}"},
                        {"name": f"Establishments.{year}"},
                    ],
                    "constraints": [
                        mapping("Area", {"King + Kitsap counties": ["53033", "53035"]}),
                        mapping("Industry", {"Restaurants": ["722511"]}),
                        employees,
                    ],
                    "limit": 2,
                },
            )
            await query(
                "location quotient and shift share",
                "industry",
                {
                    "metrics": [
                        {
                            "name": f"Jobs.{year}",
                            "as": "Concentration",
                            "operation": {
                                "name": "LocationQuotient",
                                "geoparent": "0",
                                "along": "Industry",
                            },
                        },
                        {
                            "name": f"Jobs.{year}",
                            "as": "Change factors",
                            "operation": {
                                "name": "ShiftShare",
                                "geoparent": "0",
                                "along": "Industry",
                                "base": f"Jobs.{int(year) - 5}",
                            },
                        },
                    ],
                    "constraints": [
                        mapping("Area", {"King County, WA": ["53033"]}),
                        mapping("Industry", {"Restaurants": ["722511"]}),
                        employees,
                    ],
                    "limit": 2,
                },
            )
        if metadata.get("completers"):
            year = metadata["completers"]["attributes"]["currentYear"]
            await query(
                "education completions",
                "completers",
                {
                    "metrics": [{"name": f"Completions.{year}"}],
                    "constraints": [
                        mapping("Unit", {"UW Seattle": ["236948"]}),
                        mapping("Program", {"Computer Science": ["11.0701"]}),
                        mapping("AwardLevel", {"Bachelors": ["5"]}),
                    ],
                    "limit": 2,
                },
            )
        protocol = client.protocol_version
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "mode": "core_lmi",
        "protocol_version": protocol,
        "accessible_datasets": catalog["pagination"]["total"] if catalog else None,
        "versions": versions,
        "checks": checks,
        "counts": {
            status: sum(c["status"] == status for c in checks)
            for status in ("passed", "partial", "failed")
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--core-lmi",
        action="store_true",
        help="Run Core LMI discovery and small data queries; consumes real quota.",
    )
    mode.add_argument(
        "--operations",
        action="store_true",
        help="Also run data queries; consumes API/extraction/classification quotas.",
    )
    parser.add_argument("--output", type=Path, help="Write a sanitized JSON report.")
    args = parser.parse_args()
    report = asyncio.run(
        run_core_lmi_checks() if args.core_lmi else run_checks(args.operations)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["counts"]))
    raise SystemExit(
        1 if report["counts"]["failed"] or report["counts"]["partial"] else 0
    )


if __name__ == "__main__":
    main()
