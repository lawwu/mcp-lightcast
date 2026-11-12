# Migrating from 0.2 to 0.3

This refresh corrects several public contracts. Review these changes when upgrading existing clients.

## Python requirement

The minimum Python version is now **3.14**. Python 3.12 and 3.13 are no longer supported. Upgrade the interpreter used by your MCP client or install Python 3.14 with `uv python install 3.14`, then recreate the project environment with `uv sync --python 3.14 --all-groups --frozen`. CI covers 3.14 and 3.15; Docker, documentation, and release builds use 3.14.

## API and client changes

| Before | Now |
| --- | --- |
| Default HTTP transport | Default `stdio`; request `--transport streamable-http` for HTTP |
| Hardcoded Titles `5.47`, Skills fallbacks, Classification `2025.8` | `latest` aliases or discovery of an active classifier release |
| Skills `skill_type` treated as a display name | Type IDs such as `ST1`, `ST2`, and `ST3` |
| Skills category/subcategory filters silently forwarded | Removed from the MCP tool; Python calls reject unsupported filters |
| Search/bulk skill results flatten `type` inconsistently | Skill `type` uses the API’s `{id, name}` structure |
| `find_similar_skills` returns an assumed list | Returns the upstream envelope with `data` and any warning |
| Job Postings free-form `query`, `location`, `occupation_ids`, and `version` | Native `filters`, `fields`, `limit`, and `page` |
| Benchmark `region` string and generic `version` | Region object, LOT `dimension`, and `lot_version`; `metrics` names actual datasets |
| One version passed into unrelated workflow APIs | Separate taxonomy, classifier, and LOT version parameters |
| Import from `src.mcp_lightcast` | Import from `mcp_lightcast` |
| Repository-only settings with duplicate fallbacks | One configuration implementation inside the wheel |
| `LIGHTCAST_RATE_LIMIT` (unused hourly setting) | `LIGHTCAST_REQUESTS_PER_SECOND` (enforced per service, per process) |

The old unregistered speculative Python helpers for salary insights, occupation matrices, clustering, arbitrary pathway planning, and title hierarchy were removed. Their invented endpoints were not supported by the published APIs. Use documented queries and compose analyses from real returned data.

The experimental `unified_skills` helper now delegates to the supported workflow; its old source-selection and hardcoded-mapping arguments are retired. It does not return simulated postings or benchmark data.

Update clients to read `workflow_metadata.status` and preserve upstream `warnings`. A partial result is useful, but it does not mean every requested stage succeeded.

## Core LMI and current MCP clients

Version 0.3.0 adds five Core LMI tools and upgrades to FastMCP 4 / MCP SDK 2. The 2026-07-28 protocol and legacy 2025-11-25 clients are both tested. Python code consuming SDK objects should use snake_case attributes; the generated documentation now uses `mcp.list_tools()`.

HTTP now rejects untrusted Host and Origin headers. Configure exact trusted hosts/origins for a reverse proxy; see [MCP practices](mcp-review.md). Strict argument validation also rejects previously coerced values such as a string supplied for an integer limit.
