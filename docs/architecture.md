# How the server works

An MCP client calls a registered tool. Input validation runs before the API client constructs a request. Authentication supplies a token for that service’s scope, and the shared transport handles rate spacing and bounded retries.

```text
MCP client
  └─ FastMCP tools · validated arguments / read-only annotations
      ├─ Skills / Titles
      ├─ Classification / Similarity
      ├─ Benchmarks / Career Pathways / US Job Postings
      └─ Workflows · compose clients and report partial results
          └─ Shared HTTP transport
              ├─ Service-specific OAuth token cache
              ├─ Per-service rate spacing
              └─ Lightcast API
```

## Package boundaries

| Module | Responsibility |
| --- | --- |
| `settings.py` | Lazy packaged settings and scope overrides |
| `auth/oauth.py` | Token caching, refresh, concurrency, sanitized authentication errors |
| `apis/base.py` | Service roots, HTTP requests, retries, rate limits, error types |
| `apis/` | Documented request/response contracts |
| `tools/` | MCP tools, validation, and composed workflows |
| `server.py` | Tool registration and server resources |
| `diagnostics.py` | Explicit live smoke tests and sanitized reports |

## Authentication and concurrency

Scope is an argument to authentication, never a mutable global selector. Requests to different API families cannot switch each other’s scope. Same-scope refreshes are coalesced with a lock; tokens refresh before expiry. A late `401` cannot invalidate a newer token from another request.

HTTP clients are closed when a tool finishes. Rate spacing is shared across those short-lived clients within an event loop. Locks are not reused across event loops.

## Truthful results

Wrappers preserve upstream warnings for Similarity, Career Pathways, and Occupation Benchmark. A missing dataset is not converted to a zero-valued salary or fabricated employment figure.

Workflows retain successful earlier steps when an optional downstream service fails, mark the result `partial`, and include the failed stage. A title that does not normalize returns `no_match`. Code errors are allowed to fail instead of being disguised as missing data.

## Adding a tool

Verify the endpoint against an official Lightcast specification, implement the client method, register a validated MCP tool, and add a contract test that asserts the outbound path and payload. Add an opt-in live diagnostic if the operation can be exercised with a small request. The documentation build picks up its schema automatically.
