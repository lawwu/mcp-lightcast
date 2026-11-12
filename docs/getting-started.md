# Connect in a few minutes

You need Python **3.14 or later**, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Lightcast client credentials. Request credentials through [Lightcast API access](https://lightcast.io/our-data/api/access).

## Install this version

Version **0.4.0 is published on [PyPI](https://pypi.org/project/mcp-lightcast/0.4.0/)**. Run it without a repository checkout:

```bash
uvx --python 3.14 mcp-lightcast@0.4.0 --version
```

Alternatively, install into an existing Python 3.14+ virtual environment with `python -m pip install "mcp-lightcast==0.4.0"`, then use `mcp-lightcast` directly. Existing 0.2 users should read the [migration guide](migration.md) before upgrading.

Create a local `.env` file and set:

```dotenv
LIGHTCAST_CLIENT_ID=your-client-id
LIGHTCAST_CLIENT_SECRET=your-client-secret
```

Use `LIGHTCAST_OAUTH_SCOPE=lightcast_open_free` if that is the scope assigned to your free-tier credentials. Existing `emsi_open` accounts can keep the default.

## Check your connection

```bash
uvx --python 3.14 mcp-lightcast@0.4.0 --env-file .env --validate-config
```

This makes one authentication request using your default scope. It does not prove that your account can use every premium API. For a broader check:

```bash
uvx --python 3.14 --from mcp-lightcast==0.4.0 python -m mcp_lightcast.diagnostics
```

## Connect an MCP client

Use the following configuration in a client that supports local MCP servers. Replace the environment-file path with your own absolute path. If the client cannot find `uvx`, use its absolute executable path.

```json
{
  "mcpServers": {
    "lightcast": {
      "command": "uvx",
      "args": [
        "--python", "3.14", "mcp-lightcast@0.4.0",
        "--env-file", "/absolute/path/to/lightcast.env",
        "--transport", "stdio", "--quiet"
      ]
    }
  }
}
```

The default transport is `stdio`. Startup messages and logging use stderr so stdout remains available for MCP messages.

!!! tip "Core LMI"
    The same installation includes all five Core LMI tools. Start with `list_core_lmi_datasets` to discover your account's catalog, then follow the [Core LMI examples](core-lmi.md). These tools request the `agnitio` scope automatically; access depends on your Lightcast license.

## Try a first question

> Search for Python in the Lightcast skills taxonomy. Show its ID and type, then find five related skills.

Your client should call `search_skills`, followed by `get_related_skills` with the returned ID. This keeps identifiers grounded in real results.

## Prefer HTTP?

```bash
uvx --python 3.14 mcp-lightcast@0.4.0 --env-file .env \
  --transport streamable-http --host 127.0.0.1 --port 3000
```

Connect to `http://127.0.0.1:3000/mcp`. This server uses Lightcast OAuth for outbound requests; it does not add authentication for inbound MCP clients. Keep it on localhost or place it behind an authenticated gateway.

Version 0.4.0 also supports optional caller-supplied HTTP credentials and custom providers for authorized secret stores. See [credential providers](credentials.md) for configuration and account isolation. Existing local installations can keep the default environment mode.

## Prefer Docker?

The published container includes Python and starts with stdio:

```bash
docker run --rm -i --platform linux/amd64 --env-file .env \
  ghcr.io/lawwu/mcp-lightcast:0.4.0
```

The image targets Linux amd64; Docker can emulate it on Apple Silicon. See [deployment](deployment.md) for HTTP hosting.

## Work from source

For development, clone the repository and install the locked dependencies:

```bash
git clone https://github.com/lawwu/mcp-lightcast.git
cd mcp-lightcast
uv sync --python 3.14 --all-groups --frozen
cp .env.example .env
# Add your credentials to .env before calling the API.
uv run mcp-lightcast --transport stdio
```
