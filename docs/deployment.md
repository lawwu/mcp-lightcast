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

## Package and container releases

The `Release` workflow in `.github/workflows/release.yml` runs from a pushed version tag such as `v0.3.0`. Before tagging, update the package version and lockfile, add `docs/releases/<version>.md`, and merge after the required PR checks pass. The workflow verifies that the tag matches the package version and that curated release notes exist, then runs offline tests, lint, type checks, a strict docs build, and distribution checks.

After validation, the workflow publishes to PyPI using [trusted publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/) and builds, smoke-tests, and publishes the production image to GHCR. Stable releases receive full version, minor version, and `latest` tags, for example `0.3.0`, `0.3`, and `latest`. The GitHub release is created with the curated notes and wheel/source assets only after both publishers succeed. Docker publishing is in this same workflow because releases created using `GITHUB_TOKEN` cannot trigger a second release-event workflow.

Configure the PyPI project's GitHub trusted publisher for owner `lawwu`, repository `mcp-lightcast`, workflow `release.yml`, and environment `pypi`. GHCR uses the job's `GITHUB_TOKEN` with `packages: write`; no registry password secret is needed. The container package must be public for anonymous pulls. A manual workflow run publishes only to TestPyPI and requires a separate trusted publisher there using environment `testpypi`.

If publishing fails, fix the reported credential or service problem and rerun only failed jobs. Never move an already-pushed release tag or replace a PyPI version. Successful publishers are not repeated when rerunning failed jobs, and the GitHub release job can safely update its existing notes and assets.

See the [0.3.0 release notes](releases/0.3.0.md) and [migration guide](migration.md).

## Dependency maintenance

The `Dependabot auto-merge` workflow queues verified Dependabot patch and minor updates for squash merge. Python and GitHub Actions updates are grouped separately; major upgrades are excluded from those groups and require manual review. A group containing a major update is also ineligible because the metadata action reports the highest change in the group.

The workflow only handles non-draft Dependabot branches from this repository targeting `main`. It uses `pull_request_target` for the necessary write permissions and never checks out PR code. It requires exactly one signed Dependabot commit matching the event's head, keeps the metadata action's verification enabled, and pins the merge request to that commit. Additional commits require manual review because the metadata action reads only the first commit. Each new event clears an earlier auto-merge request before revalidating. Human PRs and fork PRs are skipped; missing or unverified metadata cannot enable auto-merge. It does not approve reviews or bypass protection rules.

Repository settings must enable **Allow auto-merge** and squash merging. Branch protection for `main` must require an up-to-date branch and these checks from the GitHub Actions app:

- `Python 3.14`
- `Python 3.15`
- `docker`
- `build` (documentation)
- `Actions lock`
- `zizmor`

These requirements apply to all PRs targeting `main`. Keep the protection settings synchronized when renaming jobs or changing the Python matrix. Approval requirements added later remain in force; the workflow does not manufacture an approval. The workflow is restricted to `lawwu/mcp-lightcast`; forks must deliberately update that repository condition and configure their own protections.

The built-in `GITHUB_TOKEN` needs no additional secret, but its merges may not trigger downstream push workflows. After such a merge, run the `Documentation` workflow on `main` to refresh Pages. A dedicated GitHub App token is an option if automatic downstream push workflows become necessary. See [GitHub's workflow-trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow).

The workflow starts handling new or updated Dependabot PRs once it is merged into `main`. To opt out for a particular PR, disable its auto-merge request in GitHub; a subsequent Dependabot update will re-evaluate eligibility.

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
