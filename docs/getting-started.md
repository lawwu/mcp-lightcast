# Connect in a few minutes

You need Python **3.14 or later**, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Lightcast client credentials. Request credentials through [Lightcast API access](https://lightcast.io/our-data/api/access).

## Install this version

The refreshed implementation lives in this repository. Until version 0.3.0 is published to PyPI, run it from a checkout:

```bash
git clone https://github.com/lawwu/mcp-lightcast.git
cd mcp-lightcast
uv sync --frozen
cp .env.example .env
```

Edit `.env` and set:

```dotenv
LIGHTCAST_CLIENT_ID=your-client-id
LIGHTCAST_CLIENT_SECRET=your-client-secret
```

Use `LIGHTCAST_OAUTH_SCOPE=lightcast_open_free` if that is the scope assigned to your free-tier credentials. Existing `emsi_open` accounts can keep the default.

## Check your connection

```bash
uv run mcp-lightcast --validate-config
```

This makes one authentication request using your default scope. It does not prove that your account can use every premium API. For a broader check:

```bash
uv run python -m mcp_lightcast.diagnostics
```

## Connect an MCP client

Use the following configuration in a client that supports local MCP servers. Replace both absolute paths with your own checkout and environment file.

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

The default transport is `stdio`. Startup messages and logging use stderr so stdout remains available for MCP messages.

!!! tip "Installed package"
    Once 0.3.0 is published, `uvx --from mcp-lightcast==0.3.0 mcp-lightcast --transport stdio` will run the same version without a checkout. Do not assume an older PyPI release contains the changes documented here.

## Try a first question

> Search for Python in the Lightcast skills taxonomy. Show its ID and type, then find five related skills.

Your client should call `search_skills`, followed by `get_related_skills` with the returned ID. This keeps identifiers grounded in real results.

## Prefer HTTP?

```bash
uv run mcp-lightcast --transport streamable-http --host 127.0.0.1 --port 3000
```

Connect to `http://127.0.0.1:3000/mcp`. This server uses Lightcast OAuth for outbound requests; it does not add authentication for inbound MCP clients. Keep it on localhost or place it behind an authenticated gateway.
