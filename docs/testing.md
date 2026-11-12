# Test with confidence

## Offline regression suite

```bash
uv sync --all-groups --frozen
FASTMCP_MCP_CAMELCASE_COMPAT=false uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
```

Tests use synthetic HTTP responses shaped around the current Lightcast contracts. They cover scope isolation, concurrent token refresh, version discovery, retry bounds, MCP input validation, real tool serialization, partial workflow results, Core LMI pagination, structured output schemas, current/legacy protocol connections, and HTTP Origin/Host protection. Unmocked network calls fail during offline tests. Local `.env` credentials are replaced with test values.

## Live API checks

Metadata-only tests require an explicit flag:

```bash
uv run pytest --live -m live -v
```

The broader diagnostic runner exercises operations through an actual in-process MCP client:

```bash
uv run python -m mcp_lightcast.diagnostics --operations --output test-results/live.json
uv run python -m mcp_lightcast.diagnostics --core-lmi --output test-results/core-lmi.json
```

This consumes your account’s API quotas, including normalization and classifier requests. The report stores tool names, outcomes, version identifiers, and a timestamp. It does not store credentials, tokens, posting bodies, or raw licensed datasets. A nonzero exit means at least one operation failed or returned a partial workflow result.

An operation succeeding verifies that specific request at that time. It is not a complete inventory of account entitlements or a guarantee of unrestricted quotas. See the [dated compatibility review](review.md).

## Build and preview documentation

```bash
uv run --group docs python scripts/docs.py build --strict
uv run --group docs python scripts/docs.py serve --dev-addr 127.0.0.1:8000
```

Open the local URL printed by Zensical. Tool reference pages are regenerated from the registered server schemas during each build, without authenticating to Lightcast.

## Distribution checks

```bash
uv build
uv run twine check dist/*
```

Test a built wheel from outside the repository to catch missing package files and accidental imports from the checkout. The CLI, configuration, and health resource all import from `mcp_lightcast`, never from `src.mcp_lightcast` or a repository-only `config` directory.
