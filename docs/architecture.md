# How the server works

An MCP client calls a registered tool. Input validation runs before the API client constructs a request. Authentication supplies a token for that service’s scope, and the shared transport handles rate spacing and bounded retries.

```text
MCP client
  └─ FastMCP tools · validated arguments / read-only annotations
      ├─ Skills / Titles
      ├─ Classification / Similarity
      ├─ Benchmarks / Career Pathways / US Job Postings
      ├─ Core LMI · dataset discovery / typed queries / bounded result pages
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
| `auth/credentials.py` | Immutable credentials, asynchronous providers, request-local resolution |
| `apis/base.py` | Shared request ownership, roots, HTTP clients, timing, retries, rate limits, error types |
| `apis/` | Documented request/response contracts |
| `tools/` | MCP registration, validation, and serialization adapters |
| `workflows.py` | Composed workflows, skill evidence, provenance, and result policy |
| `server.py` | Tool registration and server resources |
| `diagnostics.py` | Explicit live smoke tests and sanitized reports |

## Authentication and concurrency

Scope is an argument to authentication, never a mutable global selector. Tokens and refresh locks are keyed by a process-keyed HMAC of the OAuth endpoint and credential pair, plus scope. Requests cannot switch each other's account or scope. Refreshes for the same key are coalesced; tokens refresh before expiry. A late `401` cannot invalidate a newer token from another request. Token and metadata caches are bounded.

`create_server(credential_provider=..., auth=...)` installs a request-local resolver. It resolves lazily once per request, so every API call in a composed workflow sees the same immutable credentials. The built-in providers read either environment settings or explicit HTTP headers, with no fallback between modes. Custom asynchronous providers can enforce caller-to-account authorization before reading a secret store. The separate FastMCP `auth` provider verifies inbound MCP identity. See [credential providers](credentials.md).

The process-shared default `RequestRuntime` owns token caching, rate state, HTTP construction, and timing. Configuration remains lazy so CLI environment loading happens before use. HTTP clients are closed when a tool finishes. Rate spacing is shared across those short-lived clients by account, OAuth endpoint, and API root within an event loop; rotating a secret does not reset account spacing. Idle rate state is reclaimed, with a cap on active entries. Locks are not reused across event loops. Distributed rate enforcement remains the deployment's responsibility.

## Explicit request ownership

Ordinary tools and Python clients use the shared default runtime. An embedding
application can pass `runtime=RequestRuntime(config)` to `create_server` to own
configuration and request state explicitly. Reuse that runtime across servers
that must share an account's token cache and rate budget. Separate explicit
runtimes have independent state; they do not enforce a combined rate budget.

For direct Python operations, select the owner with `with runtime.context():`.
The selection follows child tasks and resets on exit, including errors and
cancellation. A client retains the runtime selected when it was constructed.
Use `credential_provider_context(provider)` alongside this context when an
operation needs a custom credential provider. Runtime selection does not replace
request-local credential resolution or caller authorization.

MCP tools, OAuth health resources, and version discovery use the selected runtime.
Version metadata caches are separate for each runtime and include the requested
scope, endpoint, and credential identity.
Discovery and HTTP liveness do not resolve credentials or contact Lightcast.
`transport_factory` supplies a fresh HTTPX transport adapter for each HTTP client,
including token requests; `clock` supplies monotonic time, UTC time, and sleep.
Production uses the normal HTTP transport and system clock. Tests use a mock
transport adapter and controlled clock, asserting requests and results without
clearing private caches or patching global time.

### Runtime example

This Python example creates two server instances sharing one account's token
cache and rate budget. `LightcastConfig` reads credentials from the environment
or `.env`; constructing these objects makes no upstream requests.

```python
from mcp_lightcast.apis.base import RequestRuntime
from mcp_lightcast.server import create_server
from mcp_lightcast.settings import LightcastConfig

runtime = RequestRuntime(LightcastConfig())
first_server = create_server(runtime=runtime)
second_server = create_server(runtime=runtime)
```

Direct Python operations can use the same owner:

```python
from mcp_lightcast.workflows import analyze_job_posting_skills

async def analyze():
    with runtime.context():
        return await analyze_job_posting_skills(
            job_title="Python Developer",
            job_description="Build data pipelines with SQL.",
        )
```

Calling `analyze()` uses real Lightcast permissions and quota. Keep calls sharing
an account's rate budget on the same runtime and event loop. Separate processes
still need deployment-level rate coordination. For a custom credential provider,
pass it to `create_server` or bind `credential_provider_context(provider)` around
the direct operation. Inbound MCP authentication remains a separate concern.

## Truthful results

Core LMI resolves numeric releases through dataset metadata, uses the separate Agnitio root and scope, and applies a one-request-per-second rate. Its documented offset was ignored by the live service, so bounded prefix retrieval and local slicing prevent duplicate pages.

Wrappers preserve upstream warnings for Similarity, Career Pathways, and Occupation Benchmark. A missing dataset is not converted to a zero-valued salary or fabricated employment figure.

The composed workflow module exposes the same three operations to Python and
MCP callers. It owns client lifetimes and result assembly. Its internal skill
collection keeps first-seen details, maximum evidence strength, and all sources;
occupation scores and text-extraction confidence retain their distinct meanings.

Title-to-occupation skill inference retains successful earlier steps when an
optional downstream operation fails and marks the result `partial`. A title that
does not normalize returns `no_match`. Posting analysis and classifier extraction
require every requested stage to succeed and propagate failures. Classifier
normalization warnings remain in the normalization response; extraction warnings
remain in the top-level warnings list. Code errors fail instead of being disguised
as missing data. Existing Python workflow imports remain available through
compatibility adapters in `tools/`.

The repository’s `GLOSSARY.md` defines occupation inference, explicit skill
extraction, and partial results.

## Adding a tool

Verify the endpoint against an official Lightcast specification, implement the client method, register a validated MCP tool, and add a contract test that asserts the outbound path and payload. Add an opt-in live diagnostic if the operation can be exercised with a small request. The documentation build picks up its schema automatically.
