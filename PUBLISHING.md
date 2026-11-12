# Publishing MCP Lightcast

Package publication is separate from GitHub Pages. Documentation deploys on `main`; a package release requires a deliberate version tag.

1. Update the version in `pyproject.toml`, migration notes, and any version assertions in tests.
2. Run `uv lock`, `uv sync --all-groups --frozen`, `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src`, and `uv run --group docs python scripts/docs.py build --strict`.
3. Run `uv build` and `uv run twine check dist/*`. Test the wheel from outside the checkout.
4. Commit the release changes. A pushed `vX.Y.Z` tag triggers `.github/workflows/release.yml`, which builds, tests, and publishes with PyPI trusted publishing.

Configure the GitHub `pypi` and `testpypi` environments and the corresponding trusted publishers before releasing. The manual workflow publishes to TestPyPI only. No PyPI tokens belong in `.env.example` or the repository.

The docs for 0.3.0 describe the repository implementation. Update installation instructions once that version is available on PyPI.
