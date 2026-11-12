# Test with confidence

## Offline regression suite

CI tests Python **3.14 and 3.15**. Package metadata requires Python 3.14 or later; docs, release builds, and Docker images use 3.14. The CI matrix explicitly sets `UV_PYTHON` so each job uses its named interpreter.

```bash
uv sync --all-groups --frozen
FASTMCP_MCP_CAMELCASE_COMPAT=false uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
```

Tests use synthetic HTTP responses shaped around the current Lightcast contracts. They cover scope isolation, concurrent token refresh, version discovery, retry bounds, MCP input validation, real tool serialization, partial workflow results, Core LMI pagination, structured output schemas, current/legacy protocol connections, and HTTP Origin/Host protection. HTTP health tests check GET/HEAD, cache prevention, rejected writes, and liveness without OAuth or credentials. Unmocked network calls fail during offline tests. Local `.env` credentials are replaced with test values.

## Reverse proxy integration

Credential-isolation regressions additionally exercise concurrent HTTP callers, both protocol versions, composed workflows, authenticated health resources, and custom providers. Cases include credential rotation, rejected headers, per-account rates, sanitized errors, and bounded token caches. These use synthetic credentials; no live account is needed.

The CI Docker job builds the production image and tests it through a real nginx reverse proxy. To repeat locally, install Docker with Compose and OpenSSL, then run:

```bash
docker build -t mcp-lightcast:test .
FASTMCP_MCP_CAMELCASE_COMPAT=false uv run --frozen pytest \
  --proxy tests/integration/test_reverse_proxy.py -v
```

These tests are skipped unless `--proxy` is supplied. They create an isolated container network with the production server, nginx, and a small synthetic OAuth/Core LMI upstream. The backend has no published port or external network access. Only nginx receives a randomly assigned loopback port. A temporary TLS certificate is generated and trusted by the test client; certificate verification stays enabled. Containers and the network are removed afterward.

Coverage includes GET/HEAD health probes, discovery of all 37 tools, reading server information, and a successful Core LMI tool call preserving nulls and release metadata. Both the current 2026-07-28 protocol and legacy 2025-11-25 clients run through `/mcp` and `/lightcast/mcp`. Negative cases reject untrusted Host/Origin headers, including a spoofed forwarded hostname. The explicit proxy tests allow only loopback connections from the test client; the ordinary suite continues to reject unmocked traffic through both HTTP client libraries.

No real Lightcast credentials or quotas are used. The fixture credentials and data are synthetic; do not use the test Compose file as a production deployment. See [reverse proxy deployment](deployment.md#behind-an-nginx-reverse-proxy) for server and nginx settings.

The stack also starts a server in header mode. Concurrent synthetic accounts receive different Core LMI results through `/headers/mcp`, for both protocol versions. Missing headers cannot use the valid environment credentials intentionally configured on that server. An incorrect secret cannot reuse a cached token for the same client ID. `/headers/health` remains credential-free, and server/proxy logs are checked for the submitted synthetic secrets.

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
