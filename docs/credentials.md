# Credential providers

!!! note "Unreleased"
    These features are available in this checkout and are not included in the published v0.3.1 package or image. Run the examples with `uv run` after `uv sync --all-groups --frozen`, or build a Docker image from this checkout.

Choose how the server obtains Lightcast credentials. Local installations keep their existing configuration. HTTP callers can opt into their own credentials, and deployments can supply an asynchronous provider that retrieves an authorized credential from a secret store.

| Mode | Credential source | Intended use |
| --- | --- | --- |
| `environment` (default) | `LIGHTCAST_CLIENT_ID` and `LIGHTCAST_CLIENT_SECRET`, including `.env` | Local stdio, or a protected HTTP service using one account |
| `headers` | Two headers on each HTTP request | Controlled HTTP clients supplying their own Lightcast account |
| Custom provider | `create_server(credential_provider=..., auth=...)` | Authenticated callers mapped to credentials in your secret store |

## Local environment credentials

Existing configuration continues to work:

```dotenv
LIGHTCAST_CREDENTIAL_MODE=environment
LIGHTCAST_CLIENT_ID=your-client-id
LIGHTCAST_CLIENT_SECRET=your-client-secret
```

```bash
uv run mcp-lightcast --env-file /absolute/path/to/lightcast.env --transport stdio
```

Environment mode ignores the Lightcast credential headers. An HTTP caller cannot override the configured account in this mode. `--validate-config` still validates the environment account's default OAuth scope.

## Optional HTTP headers

Set the mode in the server's environment. No server-side Lightcast credential pair is required:

```bash
LIGHTCAST_CREDENTIAL_MODE=headers uv run mcp-lightcast \
  --transport streamable-http --host 127.0.0.1 --port 3000
```

Each caller supplies **both** `X-Lightcast-Client-Id` and `X-Lightcast-Client-Secret` on each request requiring Lightcast access. Missing, blank, duplicate, oversized, or control-character-containing values fail. Incorrect credentials fail at Lightcast. None of these cases fall back to environment credentials, even when the server has a valid pair configured.

Header mode rejects stdio and `--validate-config`, because neither has HTTP request credentials. MCP discovery, tool listings, `lightcast://server/info`, and HTTP `/health` do not require Lightcast credentials. The MCP resource `lightcast://server/health` checks the current caller's default-scope OAuth credentials.

For a FastMCP client, read credentials from its local secret configuration rather than putting them in source code or tool arguments:

```python
import asyncio
import os

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def main():
    transport = StreamableHttpTransport(
        "https://mcp.example.com/lightcast/mcp",
        headers={
            "X-Lightcast-Client-Id": os.environ["LIGHTCAST_CLIENT_ID"],
            "X-Lightcast-Client-Secret": os.environ["LIGHTCAST_CLIENT_SECRET"],
        },
    )
    # This token authenticates to your MCP service, not to Lightcast.
    async with Client(transport, auth=os.environ["MCP_ACCESS_TOKEN"]) as client:
        result = await client.call_tool("list_core_lmi_datasets", {"limit": 5})
        print(result.structured_content)


asyncio.run(main())
```

Confirm that your intended MCP clients support secure custom headers. This is a deployment-specific credential mechanism, not a replacement for MCP authorization. Protect a shared deployment with an authenticated gateway or FastMCP auth provider. The CLI does not add an identity provider. Host/Origin checks are not caller authentication.

Use HTTPS to the gateway, and a protected backend network or TLS to the server. Preserve these headers through the proxy, disable shared response caching, and exclude them from access logs, tracing, error reporting, and request captures. If a trusted gateway injects credentials, strip client-supplied values first and prevent direct backend access. Only the OAuth form sent to the administrator-configured Lightcast token endpoint contains the client secret; API requests carry a separately obtained Lightcast token. Incoming MCP bearer tokens are not forwarded upstream.

## Integrate a secret store

Implement the `CredentialProvider` protocol: `async resolve() -> LightcastCredentials`. Supply it to `create_server`, together with your MCP authentication provider. The resolver runs lazily once per MCP request that uses Lightcast, and the same immutable credential pair is used by every API client in a combined workflow. It runs again for the next request, allowing secret rotation and authorization changes to take effect.

The following adapter shows the application boundary. `store` is your deployment's implementation; the package does not include a database, secret manager, account-registration UI, or tenant mapping.

```python
from typing import Protocol

from fastmcp.server.auth import AuthProvider
from fastmcp.server.dependencies import get_access_token

from mcp_lightcast.auth.credentials import CredentialError, LightcastCredentials
from mcp_lightcast.server import create_server


class AuthorizedSecretStore(Protocol):
    async def for_principal(self, issuer: str, subject: str) -> LightcastCredentials:
        """Enforce the caller-to-account mapping, then retrieve the current secret."""
        ...


class SecretStoreProvider:
    def __init__(self, store: AuthorizedSecretStore):
        self.store = store

    async def resolve(self) -> LightcastCredentials:
        token = get_access_token()  # Verified by the configured auth provider.
        issuer = token.claims.get("iss") if token else None
        subject = token.claims.get("sub") if token else None
        if not isinstance(issuer, str) or not isinstance(subject, str):
            raise CredentialError("An authenticated account is required.")
        return await self.store.for_principal(issuer, subject)


def build_server(store: AuthorizedSecretStore, auth: AuthProvider):
    return create_server(SecretStoreProvider(store), auth=auth)
```

Configure your auth provider to validate the token signature, issuer, audience, expiry, and required permissions. For discoverable OAuth, use FastMCP's `RemoteAuthProvider` with an appropriate verifier, or another compatible provider. An identity or account name supplied in an unverified header is not authorization to retrieve its secret. Keep authorization-server discovery URLs correct when mounting behind a prefix.

Return safe messages in `CredentialError`; these are intended for the caller. Unexpected provider exceptions become a generic credential-resolution error. Do not include secrets in provider error messages or logs. The server never mutates process environment variables to switch callers.

For direct Python API usage, `credential_provider_context(provider)` binds the same resolver to an asynchronous operation and its child tasks. Use one context per operation. Providers resolve credentials only; token caching and API scopes remain the transport's responsibility.

## Isolation and cache behavior

- Tokens and refresh locks are separated by OAuth endpoint, client ID, client secret, and requested scope. A changed or incorrect secret cannot reuse a token cached for the same client ID. Cache keys are process-keyed HMACs and contain no raw credentials.
- A `401` invalidates only the affected credential/scope token, and cannot discard a newer token refreshed by another request. Failed authentication, entitlement errors, and quota errors do not replace another account's results.
- Rate spacing is shared by OAuth endpoint, account ID, and API service within each event loop. Rotating a secret does not reset that account's limiter. Different accounts have separate limiters. Multiple workers/replicas need gateway or shared rate enforcement for aggregate account budgets.
- Token caches are bounded to 1,024 entries; metadata caches to 256. Rate state retains active reservations and has a 1,024-account/service capacity per event loop. Idle rate state is reclaimed; a full active table fails safely until capacity becomes available.
- Metadata cache entries also include credential identity and API root. Request contexts are reset after success, errors, or cancellation. Secrets are excluded from credential representations and built-in error messages.

Credential rotation creates a new cache identity; it does not revoke already-issued Lightcast tokens or interrupt requests already in progress. Revoke compromised credentials/tokens through the upstream service and your deployment's secret-management process. A provider must check authorization on each resolution before returning a credential, even when a corresponding upstream token is cached.

Both supported MCP protocol versions resolve credentials per request. The current protocol is stateless; legacy session IDs are not treated as credentials or an authorization mechanism. Do not add shared per-session account state to a provider.

The [test suite](testing.md) covers concurrent accounts, composed workflows, resources, rotated and invalid credentials, independent quota failures, cache isolation, redaction, and nginx forwarding over verified HTTPS with synthetic accounts. It does not establish isolation of an external identity provider or secret store; test those deployment-specific adapters too.

See [FastMCP authentication](https://gofastmcp.com/docs/servers/auth/authentication), [FastMCP middleware](https://gofastmcp.com/docs/servers/middleware), and [MCP token audience requirements](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations).
