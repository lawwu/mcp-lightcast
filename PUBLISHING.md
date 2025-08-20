# 📦 Publishing Guide

This guide explains how to publish the MCP Lightcast package to PyPI.

## 🔑 Prerequisites

1. **PyPI Account**: Create accounts on [PyPI](https://pypi.org/account/register/) and [TestPyPI](https://test.pypi.org/account/register/)
2. **API Tokens**: Generate API tokens for both services
3. **Repository Access**: Maintainer access to this repository

## 🚀 Quick Publishing (Using .env file)

### Step 1: Configure Your .env File

Add your PyPI tokens to your `.env` file:

```bash
# Copy from example if you don't have one
cp .env.example .env

# Edit .env and add your tokens:
TEST_PYPI_TOKEN=pypi-your-testpypi-token-here
PYPI_TOKEN=pypi-your-production-token-here
```

### Step 2: Publish to Test PyPI (Recommended First)

```bash
# This will automatically load tokens from .env
make publish-test
```

### Step 3: Test Installation from Test PyPI

```bash
# Install from Test PyPI to verify it works
pip install --index-url https://test.pypi.org/simple/ mcp-lightcast

# Test the installation
mcp-lightcast --help
```

### Step 4: Publish to Production PyPI

```bash
# This will prompt for confirmation
make publish-pypi
```

## 🔧 Manual Publishing (Without .env)

If you prefer to set environment variables manually:

```bash
# Set credentials
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here

# Build and check
make build-dist
make check-dist

# Upload manually
uv run twine upload --repository testpypi dist/*  # Test PyPI
uv run twine upload dist/*                        # Production PyPI
```

## 📋 Publishing Checklist

Before publishing a new version:

- [ ] **Update Version**: Update `version = "x.y.z"` in `pyproject.toml`
- [ ] **Update CHANGELOG**: Document changes (if applicable)
- [ ] **Test Locally**: Run `make check` to ensure all tests pass
- [ ] **Build Clean**: Run `make clean && make build-dist`
- [ ] **Test PyPI First**: Always test on TestPyPI before production
- [ ] **Verify Installation**: Install from TestPyPI and test functionality
- [ ] **Create Git Tag**: Tag the release with `git tag -a vx.y.z -m "Release vx.y.z"`
- [ ] **Production Release**: Publish to production PyPI
- [ ] **Push Tags**: Push tags to GitHub with `git push origin --tags`

## 🎯 Version Management

This project uses **static versioning**:

1. **Update Version**: Edit `version = "x.y.z"` in `pyproject.toml`
2. **Commit Changes**: Commit all changes including version bump
3. **Create Tag**: `git tag -a vx.y.z -m "Release vx.y.z"`
4. **Build & Publish**: Follow publishing steps above

## 🔄 GitHub Actions (Automatic)

For automatic publishing via GitHub Actions:

1. **Set Repository Secrets**:
   - Go to GitHub Repository → Settings → Secrets and Variables → Actions
   - Add `PYPI_API_TOKEN` with your production PyPI token
   - Add `TEST_PYPI_API_TOKEN` with your TestPyPI token

2. **Trigger Release**:
   ```bash
   # Create and push a version tag
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

3. **Automatic Process**:
   - GitHub Actions will build, test, and publish automatically
   - Creates GitHub Release with auto-generated release notes
   - Publishes to PyPI and creates Docker images

## 🛠️ Available Make Commands

```bash
make build-dist     # Build distribution packages
make check-dist     # Validate distribution packages
make publish-test   # Publish to Test PyPI (loads .env)
make publish-pypi   # Publish to production PyPI (loads .env)
make release        # Run release preparation script
```

## 🔍 Troubleshooting

### Common Issues

**"No PyPI token found"**
- Ensure your `.env` file contains `TEST_PYPI_TOKEN` or `PYPI_TOKEN`
- Check token format starts with `pypi-`

**"Package already exists"**
- Version already published to PyPI
- Increment version in `pyproject.toml`

**"Invalid credentials"**
- Check your API token is correct
- Verify token has upload permissions
- For TestPyPI, ensure you're using TestPyPI token

**"Build fails"**
- Run `make clean` then `make build-dist`
- Check all dependencies in `pyproject.toml`

### Getting Help

- Check [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- Review [Twine Documentation](https://twine.readthedocs.io/)
- Open an issue in this repository

## 🏷️ Current Status

- **Version**: 0.1.0
- **PyPI Package**: [mcp-lightcast](https://pypi.org/project/mcp-lightcast/)
- **Test PyPI**: [mcp-lightcast](https://test.pypi.org/project/mcp-lightcast/)
- **License**: MIT