# Practical recipes

The snippets below are MCP tool arguments. Start your server using the [quick start](getting-started.md), then use these through an MCP client.

## Find specialized Python skills

Tool: `search_skills`

```json
{"query": "Python", "limit": 5, "skill_type": "ST1"}
```

Use a returned ID with `get_skill_details` or `get_related_skills`. Avoid guessing skill IDs from names.

## Understand a role

Tool: `normalize_title_and_get_skills`

```json
{
  "raw_title": "Senior software engineer",
  "max_occupations": 3,
  "max_skills_per_occupation": 10,
  "confidence_threshold": 0.6
}
```

Check `workflow_metadata.status`. A `partial` result contains useful completed steps and an `errors` list; it is not a complete skill profile. If no title or occupation matches, that status is returned explicitly.

## Compare two occupations

Tool: `get_career_skill_gap`

```json
{
  "source_id": "11-1021",
  "destination_id": "11-1011",
  "dimension": "soc",
  "nation": "us",
  "limit": 10
}
```

Both IDs must belong to the same taxonomy. Use `get_pathways_metadata` to confirm supported dimensions.

## Benchmark a LOT occupation

Tool: `get_occupation_benchmark`

```json
{
  "occupation_id": "231715",
  "dimension": "lotocc",
  "metrics": ["taxonomicalInfo", "salary", "demand"],
  "region": {"nation": "us"}
}
```

Read the response’s top-level `warnings`: requested datasets can be unavailable even when the HTTP request succeeds.

## Investigate demand in a city

Tool: `get_posting_statistics`

```json
{
  "filters": {"when": "active", "city_name": ["Seattle, WA"], "title": ["ET6850661D6AE5FA86"]},
  "metrics": ["unique_postings", "median_salary"]
}
```

The `when` filter is required. Use `"active"` for current postings or an object with `start` and `end` months for a bounded study. Confirm available months with `get_postings_metadata`. The native filter contract is documented in [US Job Postings](https://docs.lightcast.io/lightcast-api/reference/jpa_post_totals).

## Call through Python

```python
import asyncio
from fastmcp import Client
from mcp_lightcast.server import mcp

async def main():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_skills", {"query": "Python", "limit": 3}
        )
        # List-returning tools are wrapped in {"result": [...]} by MCP.
        print(result.structured_content)

asyncio.run(main())
```

## Employment, wages, industries, and education

See the [Core LMI guide](core-lmi.md) for verified query examples: compare software-developer employment and earnings across states, combine counties into a custom region, request location quotients and shift-share components, and examine computer-science completions at an institution.
