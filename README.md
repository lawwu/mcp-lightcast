# MCP Lightcast

**Lightcast’s labor-market intelligence, connected to your AI tools.**

[Documentation](https://lawwu.github.io/mcp-lightcast/) · [Tool reference](https://lawwu.github.io/mcp-lightcast/reference/tools/) · [PyPI](https://pypi.org/project/mcp-lightcast/0.3.1/) · [v0.3.1 release notes](https://github.com/lawwu/mcp-lightcast/releases/tag/v0.3.1)

37 MCP tools for Skills, Titles, Classification, Similarity, Occupation Benchmark, Career Pathways, US Job Postings, and Core LMI. Built with Python 3.14+, FastMCP 4, and scope-specific OAuth authentication.

## Install v0.3.1

Version **0.3.1** is available on PyPI and requires **Python 3.14 or newer**. With [uv installed](https://docs.astral.sh/uv/getting-started/installation/), run the published package without cloning this repository:

```bash
uvx --python 3.14 mcp-lightcast@0.3.1 --version
```

Alternatively, install into an existing Python 3.14+ virtual environment with `python -m pip install "mcp-lightcast==0.3.1"`, then use the `mcp-lightcast` command directly.

**Upgrading from 0.2?** Review the [migration guide](https://lawwu.github.io/mcp-lightcast/migration/) for the higher Python requirement, default stdio transport, and breaking Skills, Job Postings, and Occupation Benchmark tool changes.

### Configure your credentials

Create a local `.env` file containing:

```dotenv
LIGHTCAST_CLIENT_ID=your-client-id
LIGHTCAST_CLIENT_SECRET=your-client-secret
```

[Get Lightcast credentials](https://lightcast.io/our-data/api/access). Free-tier accounts may need `LIGHTCAST_OAUTH_SCOPE=lightcast_open_free`. Premium endpoints require their own permissions and quotas.

From the directory containing `.env`, check authentication and start the server:

```bash
uvx --python 3.14 mcp-lightcast@0.3.1 --env-file .env --validate-config
uvx --python 3.14 mcp-lightcast@0.3.1 --env-file .env --transport stdio
```

The authentication check validates the default scope; it does not establish access to every API or Core LMI dataset.

### Connect your MCP client

For a client that launches local MCP servers, use the following configuration. Replace the environment-file path with your own absolute path; no repository checkout is needed. If your client cannot find `uvx`, use its absolute executable path.

```json
{
  "mcpServers": {
    "lightcast": {
      "command": "uvx",
      "args": [
        "--python", "3.14", "mcp-lightcast@0.3.1",
        "--env-file", "/absolute/path/to/lightcast.env",
        "--transport", "stdio", "--quiet"
      ]
    }
  }
}
```

For HTTP:

```bash
uvx --python 3.14 mcp-lightcast@0.3.1 --env-file .env \
  --transport streamable-http --host 127.0.0.1 --port 3000
```

Connect to `http://127.0.0.1:3000/mcp`. Keep HTTP local or use an authenticated gateway; inbound MCP authentication is not built in.

New in **v0.3.1**, `GET /health` returns `{"status":"ok"}` without contacting Lightcast; HEAD is also supported. See the [health and reverse proxy guide](https://lawwu.github.io/mcp-lightcast/deployment/#http-health-endpoint) for monitoring and the nginx configuration tested with HTTPS, path prefixes, and both MCP protocol versions.

### Docker

The published image includes Python and the server:

```bash
docker run --rm -i --platform linux/amd64 --env-file .env \
  ghcr.io/lawwu/mcp-lightcast:0.3.1
```

The image targets Linux amd64; Docker can emulate it on Apple Silicon. Moving tags `0.3` and `latest` are also available. See [deployment](https://lawwu.github.io/mcp-lightcast/deployment/) for HTTP hosting.

## What you can do

| Task | Tools |
| --- | --- |
| Search, retrieve, and extract skills | `search_skills`, `get_skill_details`, `bulk_retrieve_skills`, `extract_skills_from_text` |
| Normalize job titles | `search_job_titles`, `normalize_job_title`, `get_job_title_details` |
| Classify and map occupations | `classify_occupation`, `list_taxonomy_mappings`, `map_taxonomy_concepts` |
| Compare skills and careers | `query_similarity`, `get_career_next_steps`, `get_career_skill_gap` |
| Investigate demand and pay | `search_job_postings`, `get_posting_statistics`, `get_posting_rankings`, `get_occupation_benchmark` |
| Explore employment, wages, and education | Core LMI tools below |
| Combine APIs | `normalize_title_and_get_skills`, `analyze_job_posting_skills` |

Use metadata tools to discover fields and supported versions. Workflows preserve IDs, provenance, warnings, and partial failures. They never invent benchmark or career results.

## Core LMI support

New in **v0.3.0**, Core LMI (Agnitio) provides employment, earnings, industry, education, and regional measures. It uses your existing Lightcast credentials and automatically requests the separate `agnitio` scope. Your Lightcast license determines which datasets you can query.

| Tool | Purpose |
| --- | --- |
| `list_core_lmi_datasets` | Discover the datasets available to your account |
| `get_core_lmi_versions` | Find available releases for a dataset |
| `get_core_lmi_metadata` | Inspect measures, dimensions, and query capabilities |
| `get_core_lmi_dimension` | Look up valid occupation, industry, region, or institution codes |
| `query_core_lmi` | Query measures, combine regions, and calculate location quotients or shift-share components where supported |

Try asking your assistant:

- “Compare software developer employment and median annual earnings in California and Washington.”
- “How many restaurant jobs are in King and Kitsap counties combined, and how concentrated is the industry locally?”
- “How many computer science bachelor's awards did UW Seattle report?”

Start with dataset discovery, inspect the release and metadata, then query using the returned codes. Core LMI describes labor-market measures and projections; Job Postings describes advertised demand.

The release review passed **18 live Core LMI checks** against occupation, industry, and education-completions data. The tested account exposed 52 datasets; that catalog is account-specific. See the [Core LMI guide](https://lawwu.github.io/mcp-lightcast/core-lmi/) for verified JSON examples, pagination limits, and the known cost-of-living query limitation, and the [API review](https://lawwu.github.io/mcp-lightcast/review/) for test details.

## Develop and test

To work on the source:

```bash
git clone https://github.com/lawwu/mcp-lightcast.git
cd mcp-lightcast
uv sync --python 3.14 --all-groups --frozen
cp .env.example .env             # Add credentials only for live API use
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

Both diagnostic commands consume real API quotas. Their reports contain only tool outcomes and version metadata.

## Dependency updates

Dependabot patch and minor updates are eligible for automatic squash merge after required checks pass. Major updates remain for manual review. See [dependency maintenance](docs/deployment.md#dependency-maintenance) for the policy and required repository settings.

## Documentation deployment

The docs use Zensical with custom styling, search, light/dark themes, and a tool reference generated from actual MCP schemas. GitHub Actions builds pull requests and deploys `main` to GitHub Pages. Set **Settings → Pages → Source → GitHub Actions** once. No Lightcast secrets are needed for documentation builds.

See [deployment](docs/deployment.md), [configuration](docs/configuration.md), and the [0.3 migration guide](docs/migration.md). This is an independent MIT-licensed project, not an official Lightcast product.
