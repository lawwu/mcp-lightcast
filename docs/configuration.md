# Configuration

The installed package and repository checkout use the same configuration. Values come from environment variables first, then the working directory’s `.env`. `--env-file` loads a specific file before clients are created; existing environment variables take precedence.

## Lightcast connection

| Variable | Default | Purpose |
| --- | --- | --- |
| `LIGHTCAST_CLIENT_ID` | Required | OAuth client ID |
| `LIGHTCAST_CLIENT_SECRET` | Required | OAuth client secret |
| `LIGHTCAST_OAUTH_SCOPE` | `emsi_open` | Scope for Skills and Titles; free-tier accounts may need `lightcast_open_free` |
| `LIGHTCAST_OAUTH_URL` | `https://auth.emsicloud.com/connect/token` | Token endpoint |
| `LIGHTCAST_BASE_URL` | `https://api.lightcast.io` | Root for all API families except Classification |
| `LIGHTCAST_CLASSIFICATION_URL` | `https://classification.emsicloud.com` | Classification root |
| `LIGHTCAST_API_SCOPES` | `{}` | JSON object overriding scopes by API family |
| `LIGHTCAST_REQUESTS_PER_SECOND` | `5` | Per-service request rate within this process |
| `LIGHTCAST_TIMEOUT` | `30` | Request timeout in seconds |
| `LIGHTCAST_MAX_RETRIES` | `2` | Retries for transient gateway failures and short `Retry-After` responses |

## API scopes

| API | Default scope |
| --- | --- |
| Skills, Titles | `LIGHTCAST_OAUTH_SCOPE` |
| Classification | `classification_api` |
| Similarity | `similarity` |
| Occupation Benchmark | `occupation-benchmark` |
| Career Pathways | `career-pathways` |
| US Job Postings | `postings:us` |

For an account assigned `lightcast_open` for Classification:

```dotenv
LIGHTCAST_API_SCOPES={"classification":"lightcast_open"}
```

Tokens are cached separately for each requested scope. A successful token request does not establish entitlement to every endpoint. Normalization, extraction, postings, and premium datasets may have additional permissions or quotas. See [Lightcast authentication](https://docs.lightcast.io/lightcast-api/docs/authentication-guide).

## Server options

`MCP_SERVER_NAME` defaults to `lightcast-mcp-server`. `MASK_ERROR_DETAILS=true` hides tool exception details from MCP clients. The CLI supports `--log-level`, `--quiet`, `--host`, `--port`, `--transport`, and `--validate-config`.

## Versions that mean different things

| Parameter | Meaning |
| --- | --- |
| Skills `version` | Skills taxonomy version, or `latest` |
| Titles `version` | Titles taxonomy version, or `latest` |
| Classification `version` | Classifier release; `latest` is resolved through `/classifications` |
| `lot_version` | LOT major version supported by the model, currently `6` or `7` |
| JPA data | Discover available months and taxonomy versions through metadata |

Combined workflows expose separate version parameters. Do not pass a Skills taxonomy version into a title or classifier request. For reproducible research, record metadata and pin compatible versions; classifier releases can expire.

## Rate limits and errors

The client spaces requests across short-lived clients for each service. Limits are process-local; multiple server processes still share your account quota.

A `401` refreshes only the token for the affected scope and retries once. `403` fails immediately. `502`, `503`, and `504` use bounded backoff. `429` is retried only when `Retry-After` is present and at most five seconds. Longer or unspecified delays produce a quota error with reset information for Python callers.
