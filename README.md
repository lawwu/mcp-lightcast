# MCP Lightcast

**Lightcast’s labor-market intelligence, connected to your AI tools.**

[Documentation](https://lawwu.github.io/mcp-lightcast/) · [Tool reference](https://lawwu.github.io/mcp-lightcast/reference/tools/) · [API review](docs/review.md)

37 MCP tools for Skills, Titles, Classification, Similarity, Occupation Benchmark, Career Pathways, US Job Postings, and Core LMI. Built with Python 3.14+, FastMCP 4, and scope-specific OAuth authentication.

## Quick start

Version 0.3.0 is the repository refresh; run from this checkout until it is published to PyPI.

```bash
uv sync --frozen
cp .env.example .env
# Add LIGHTCAST_CLIENT_ID and LIGHTCAST_CLIENT_SECRET to .env.
uv run mcp-lightcast --validate-config
uv run mcp-lightcast --transport stdio
```

[Get Lightcast credentials](https://lightcast.io/our-data/api/access). Free-tier accounts may need `LIGHTCAST_OAUTH_SCOPE=lightcast_open_free`. Premium endpoints require their own permissions and quotas.

For an MCP client that launches local servers:

```json
{
  "mcpServers": {
    "lightcast": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/mcp-lightcast",
        "run", "mcp-lightcast",
        "--env-file", "/absolute/path/to/mcp-lightcast/.env",
        "--transport", "stdio", "--quiet"
      ]
    }
  }
}
```

For HTTP, run `uv run mcp-lightcast --transport streamable-http --port 3000` and connect to `http://127.0.0.1:3000/mcp`. Keep HTTP local or use an authenticated gateway; inbound MCP authentication is not built in.

## What you can do

| Task | Tools |
| --- | --- |
| Search, retrieve, and extract skills | `search_skills`, `get_skill_details`, `bulk_retrieve_skills`, `extract_skills_from_text` |
| Normalize job titles | `search_job_titles`, `normalize_job_title`, `get_job_title_details` |
| Classify and map occupations | `classify_occupation`, `list_taxonomy_mappings`, `map_taxonomy_concepts` |
| Compare skills and careers | `query_similarity`, `get_career_next_steps`, `get_career_skill_gap` |
| Investigate demand and pay | `search_job_postings`, `get_posting_statistics`, `get_posting_rankings`, `get_occupation_benchmark` |
| Explore employment, wages, and education | `list_core_lmi_datasets`, `get_core_lmi_metadata`, `get_core_lmi_dimension`, `query_core_lmi` |
| Combine APIs | `normalize_title_and_get_skills`, `analyze_job_posting_skills` |

See [Core LMI examples](docs/core-lmi.md) for employment comparisons, custom regions, industry concentration, and education completions, and the [MCP practices review](docs/mcp-review.md) for the protocol upgrade.

Use metadata tools to discover fields and supported versions. Workflows preserve IDs, provenance, warnings, and partial failures. They never invent benchmark or career results.

## Develop and test

```bash
uv sync --all-groups --frozen
uv run pytest                    # Offline by default; no API credentials needed
uv run ruff check src tests
uv run mypy src
uv run --group docs python scripts/docs.py serve # Local docs with live reload
```

Explicit live checks:

```bash
uv run pytest --live -m live
uv run python -m mcp_lightcast.diagnostics --operations --output test-results/live.json
uv run python -m mcp_lightcast.diagnostics --core-lmi --output test-results/core-lmi.json
```

Both diagnostic commands consume real API quotas. Its report contains only tool outcomes and version metadata.

## Dependency updates

Dependabot patch and minor updates are eligible for automatic squash merge after required checks pass. Major updates remain for manual review. See [dependency maintenance](docs/deployment.md#dependency-maintenance) for the policy and required repository settings.

## Documentation deployment

The docs use Zensical with custom styling, search, light/dark themes, and a tool reference generated from actual MCP schemas. GitHub Actions builds pull requests and deploys `main` to GitHub Pages. Set **Settings → Pages → Source → GitHub Actions** once. No Lightcast secrets are needed for documentation builds.

See [deployment](docs/deployment.md), [configuration](docs/configuration.md), and the [0.3 migration guide](docs/migration.md). This is an independent MIT-licensed project, not an official Lightcast product.
