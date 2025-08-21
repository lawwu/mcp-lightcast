# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Lightcast is a Model Context Protocol (MCP) server that provides FastMCP-based integration with Lightcast APIs for job titles, skills analysis, and career data. The project is built using Python 3.12+ and follows modern Python development practices.

**Current Status**: v0.2.0 - Production ready with 11/18 API endpoints working (61% coverage)

## Essential Commands

### Development Setup
```bash
make setup                    # Initial project setup (installs deps, creates .env)
make install-dev              # Install all dependencies including dev
uv sync --all-groups          # Sync all dependencies from lockfile
```

### Running the Server
```bash
make run                      # Run MCP server (streamable-http, port 3000)
make run-stdio                # Run with stdio transport (for Claude Desktop)
make dev-server               # Run with debug logging
make validate-config          # Validate configuration and test auth
```

### Code Quality & Testing
```bash
make check                    # Run all checks (lint + type-check + test)
make lint                     # Run ruff linting
make type-check               # Run mypy type checking
make format                   # Format with black and ruff
make test                     # Run pytest tests
make test-coverage            # Run tests with coverage report
make test-apis-manual         # Test with real API calls (requires credentials)
```

### Environment Configuration
```bash
make test-env-check           # Check if API credentials are configured
make claude-config            # Show Claude Desktop integration config
```

## Architecture Overview

### Core Components

**Entry Points**:
- `src/mcp_lightcast/__init__.py` - Main CLI entry point with Click framework
- `src/mcp_lightcast/__main__.py` - Module execution entry point  
- `src/mcp_lightcast/server.py` - FastMCP server instance and tool registration

**API Layer Architecture**:
- `src/mcp_lightcast/apis/base.py` - Base HTTP client with OAuth2 auth, rate limiting, error handling
- `src/mcp_lightcast/apis/` - Individual API clients (titles, skills, classification, etc.)
- `src/mcp_lightcast/auth/oauth.py` - OAuth2 client credentials flow with token caching

**MCP Tools Layer**:
- `src/mcp_lightcast/tools/` - FastMCP tool registrations organized by API category
- `src/mcp_lightcast/tools/workflow_tools.py` - Combined workflows (title normalization + skills)
- `src/mcp_lightcast/tools/unified_skills_tools.py` - Unified skills interface

**Configuration**:
- `config/settings.py` - Pydantic settings with environment variable binding
- `.env` file - Local environment configuration (not committed)

### Key Architectural Patterns

**Dynamic OAuth Scoping**: Base client automatically switches OAuth scopes based on API requirements. Each API has specific scope requirements defined in `API_SCOPES` mapping.

**API-Specific Base URLs**: Each Lightcast API uses different base URLs (e.g., `emsiservices.com` vs `emsicloud.com`). The base client handles this via `API_BASE_URLS` mapping.

**Version Management**: All API calls support a `version` parameter with "latest" as default. The system handles version resolution automatically.

**Error Handling Chain**: Base client handles HTTP errors, rate limits (429), and authentication failures. API-specific clients handle business logic errors.

**Tool Registration Pattern**: Each API category has its own tool registration module that registers multiple related FastMCP tools.

## API Coverage & Limitations

### Working APIs (11/18 endpoints)
- **Skills API**: Search, details, extraction from text, bulk retrieval, metadata
- **Titles API**: Search, details, bulk retrieval, metadata
- **Classification/Workflow**: Skills extraction workflows

### Limited/Premium Features
- **Title Normalization**: Requires premium scope (currently returns 401)
- **Skills Categories**: Endpoint not available in current API version
- **Related Skills/Titles**: Endpoint patterns differ from documentation

### Authentication Scopes
- **Public APIs** (`emsi_open`): Skills search/details, Titles search/details
- **Premium APIs**: Classification, Similarity, Occupation Benchmark, Career Pathways, Job Postings

## Testing Strategy

### Test Types
- **Unit Tests** (`tests/unit/`): Mock all HTTP calls, test business logic
- **Integration Tests** (`tests/integration/`): Test server components with mocked APIs  
- **Manual API Tests** (`tests/manual_api_integration.py`): Real API calls with credentials

### Test Commands
```bash
make test                     # Unit + integration tests
make test-apis-manual         # Manual tests with real API (requires .env)
make test-env-check           # Verify API credentials are configured
make ci                       # Full CI pipeline locally
```

### Test Configuration
- `tests/conftest.py` - Comprehensive pytest fixtures for all API clients
- Mock objects follow the real API client interfaces exactly
- Sample responses mirror actual Lightcast API response structures

## Development Patterns

### Adding New API Endpoints

1. **API Client** - Extend existing client in `src/mcp_lightcast/apis/` or create new one
2. **MCP Tools** - Add tool registration in appropriate `*_tools.py` file
3. **Server Registration** - Import and register tools in `server.py`
4. **Tests** - Add unit tests with mocks and manual integration tests

### Environment Configuration

The project uses fallback configuration loading:
- Primary: `config/settings.py` with Pydantic settings
- Fallback: Inline Pydantic classes when config module unavailable
- Environment: `.env` file or system environment variables

### OAuth Token Management

The auth system handles:
- **Token Caching**: Tokens cached until 60 seconds before expiration
- **Scope Switching**: Different tokens for different API scopes
- **Automatic Refresh**: Transparent token renewal on expiration
- **Error Recovery**: Graceful handling of auth failures

### Version Strategy

- **Default**: Use "latest" for all API calls
- **Override**: Specific versions can be passed to any API call  
- **Backward Compatible**: Support for older API versions when needed

## Important Configuration

### Required Environment Variables
```bash
LIGHTCAST_CLIENT_ID=your_client_id
LIGHTCAST_CLIENT_SECRET=your_client_secret
```

### Optional Configuration
```bash
LIGHTCAST_BASE_URL=https://api.lightcast.io
LIGHTCAST_OAUTH_URL=https://auth.emsicloud.com/connect/token
LIGHTCAST_OAUTH_SCOPE=emsi_open
MCP_SERVER_NAME=lightcast-mcp-server
LOG_LEVEL=INFO
```

### Claude Desktop Integration
Use `make claude-config` to generate the correct configuration for Claude Desktop integration with uv.

## Dependencies

**Core**: FastMCP 2.11.0+, httpx, Pydantic 2.0+, python-dotenv, Click
**Dev**: pytest, pytest-asyncio, pytest-httpx, black, ruff, mypy, pre-commit
**Python**: 3.12+ required (uses modern typing features)
**Package Manager**: uv (recommended) or pip

## Common Issues

**Authentication Failures**: Check credentials with `make test-env-check`
**Rate Limiting**: Manual tests may hit API limits - use delays if needed
**Premium Features**: Some APIs require paid Lightcast access beyond `emsi_open` scope
**Version Conflicts**: Use `uv sync --all-groups` to resolve dependency issues