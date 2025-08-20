#!/bin/bash
set -e

echo "🚀 MCP Lightcast Release Publisher"
echo "=================================="

# Check if we're on the right branch and have clean working directory
if [[ $(git status --porcelain) ]]; then
    echo "❌ Working directory is not clean. Please commit or stash changes."
    exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "❌ Not on main branch. Please switch to main branch."
    exit 1
fi

# Get version from tag
VERSION=$(git describe --tags --exact-match 2>/dev/null || echo "")
if [[ -z "$VERSION" ]]; then
    echo "❌ No version tag found. Please create a version tag first."
    echo "Example: git tag -a v0.1.0 -m 'Release v0.1.0'"
    exit 1
fi

echo "📦 Building version: $VERSION"

# Clean and build
rm -rf dist/
uv build

# Check the distribution
echo "🔍 Checking distribution..."
uv run twine check dist/*

echo ""
echo "✅ Distribution check passed!"
echo ""
echo "📋 Ready to publish:"
echo "   - Version: $VERSION"
echo "   - Files:"
ls -la dist/

echo ""
echo "🎯 Publishing options:"
echo "1. Test PyPI (recommended first): make publish-test"
echo "2. Production PyPI: make publish-pypi"
echo ""
echo "Or run manually:"
echo "   uv run twine upload --repository testpypi dist/*"
echo "   uv run twine upload dist/*"
echo ""
echo "🔑 Make sure you have your PyPI API tokens configured:"
echo "   ~/.pypirc or set TWINE_USERNAME and TWINE_PASSWORD"