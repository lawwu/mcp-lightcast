# Deploy the docs and server

The documentation is a static website. The MCP server runs separately and keeps your Lightcast credentials on the machine hosting it.

## Automatic GitHub Pages deployment

The `Documentation` workflow in `.github/workflows/docs.yml`:

1. Builds the site on pull requests, pushes to `main`, and manual runs.
2. Installs locked Python dependencies with `uv`.
3. Generates the tool reference from current server schemas.
4. Runs `python scripts/docs.py build --strict` so broken documentation links fail the build.
5. Uploads the static site and deploys pushes to `main` using GitHub’s Pages actions.

In the repository, set **Settings → Pages → Build and deployment → Source → GitHub Actions**. The workflow needs `pages: write` and `id-token: write` only in its deployment job. Pull requests build without receiving deployment permissions.

The configured site URL is:

[lawwu.github.io/mcp-lightcast](https://lawwu.github.io/mcp-lightcast/)

Forks should update `site_url`, `repo_url`, and package links. If a deployment waits for environment approval, review the repository’s `github-pages` environment protection rules.

No Lightcast credentials are needed in GitHub Actions to build or deploy the docs. `.env` is excluded from Git, distributions, and Docker contexts.

## Local MCP server

```bash
uv run mcp-lightcast --transport stdio
```

For local HTTP access:

```bash
uv run mcp-lightcast --transport streamable-http --host 127.0.0.1 --port 3000
```

## Docker

```bash
docker build -t mcp-lightcast .
docker run --rm -i --env-file .env mcp-lightcast
```

For HTTP, publish only the local interface unless an authenticated gateway is configured:

```bash
docker run --rm --env-file .env -p 127.0.0.1:3000:3000 mcp-lightcast \
  --transport streamable-http --host 0.0.0.0 --port 3000
```

The container runs as a non-root user. No credentials are included in the image. GitHub Pages cannot host this Python MCP process; it serves only the documentation.
