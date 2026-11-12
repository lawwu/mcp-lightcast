# MCP compatibility and practices

**Reviewed November 12, 2026.** The current published MCP revision is **2026-07-28**. This branch upgrades FastMCP from 2.14 to **4.1.8** and the Python MCP SDK to **2.3.0** in the lockfile. Framework versions and protocol revisions are separate identifiers.

## Applied in this update

| Practice | Implementation and evidence |
| --- | --- |
| Support current clients while retaining earlier clients | FastMCP 4 serves the 2026-07-28 protocol and legacy initialization-based clients. Tests exercise both current and 2025-11-25 connections. |
| Validate HTTP origins and hosts | The CLI explicitly enables `host_origin_protection=True`; HTTP still binds to `127.0.0.1` by default. Tests reject an external Origin, the null Origin, and an untrusted Host. |
| Give clients usable schemas | Core LMI inputs and outputs use Pydantic models, including query operations, constraints, and pagination. A protocol test validates the returned structured result against its advertised output schema. |
| Fail clearly without leaking upstream details | Sanitized API and authentication errors are MCP tool errors. Tests assert `isError` and actionable HTTP/scope information while excluding raw upstream response bodies. Unexpected errors remain masked. |
| Validate before spending quota | Strict MCP input validation rejects wrong types, invalid limits, unknown query fields, and malformed constraints before network access. |
| Describe tool effects | Every tool declares read-only, non-destructive, idempotent, open-world behavior. API calls still consume quota. |
| Keep catalogs deterministic | Tools are registered in a fixed order; repeated discovery is tested for identical ordering. |
| Report server identity and intended use | Discovery includes the package version, documentation URL, and guidance to inspect metadata, preserve provenance, and treat upstream text as data. |
| Bound responses and preserve meaning | Core LMI pages have explicit limits, release provenance, and column structure. Missing values remain missing. Native offset behavior is handled explicitly. |
| Preserve cancellation and channel discipline | Async requests remain cancellable; stdio reserves stdout for protocol messages and uses stderr for logs. |

## Transport changes belong in the framework

The 2026-07-28 specification changes discovery, per-request metadata, result types, sessions, and notification delivery. This server uses the current SDK’s implementation instead of maintaining custom JSON-RPC transport logic. Existing tools and resources remain available to legacy clients.

FastMCP’s default client mode probes the server and selects a mutually supported protocol. SDK model attributes now use Python snake_case; tests run with the deprecated camelCase compatibility bridge disabled. Lightcast’s own payload fields, such as `dimensionName`, remain unchanged.

## Deployment boundaries

The default is a local stdio server. HTTP remains a single-account interface using the configured Lightcast credentials. Host/Origin protection is a request check, not authentication or CORS. Before exposing the service to other people, add inbound authentication and an authorization policy for the account and licensed datasets. Never accept a caller’s arbitrary bearer token and forward it to Lightcast.

For a trusted reverse proxy, configure the precise hostname and browser origins instead of disabling protection:

```bash
FASTMCP_HTTP_ALLOWED_HOSTS='["mcp.example.com"]'
FASTMCP_HTTP_ALLOWED_ORIGINS='["https://trusted-client.example.com"]'
```

These are environment variables for the server process. They do not authenticate a client. The environment may be supplied through the CLI’s `--env-file`. Keep the external authentication gateway in place.

No shared result cache is enabled. Core LMI availability and responses are account-specific; any future cache must be partitioned by authorization context and release. Health checks should not inherit a long-lived catalog cache.

## Follow-up choices

- Add OAuth-based inbound authentication when moving from local use to a shared hosted server.
- Add resource templates or reusable prompts when a concrete client workflow needs them. The five Core LMI tools currently provide discovery and queries to clients that only support tools.
- Consider tool search if the catalog grows substantially. The current 37-tool catalog is kept explicit and stable.
- Add long-running task support only if queries outgrow the current bounded request model.

## Sources

- [Current specification changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog).
- [Version compatibility](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning).
- [Tool schemas, errors, and annotations](https://modelcontextprotocol.io/specification/2026-07-28/server/tools).
- [HTTP security requirements](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http).
- [Local server practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security).
- [FastMCP 4 overview](https://gofastmcp.com/docs/getting-started/whats-new), [upgrade from 2](https://gofastmcp.com/docs/getting-started/upgrading/from-fastmcp-2), [upgrade from 3](https://gofastmcp.com/docs/getting-started/upgrading/from-fastmcp-3), and [HTTP protections](https://gofastmcp.com/docs/deployment/http#host-and-origin-protection).
