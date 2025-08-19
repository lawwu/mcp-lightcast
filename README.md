# MCP Lightcast Server

[![CI/CD Pipeline](https://github.com/your-org/mcp-lightcast/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-org/mcp-lightcast/actions)
[![Docker Pulls](https://img.shields.io/docker/pulls/mcp-lightcast/mcp-lightcast)](https://hub.docker.com/r/mcp-lightcast/mcp-lightcast)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A production-ready Model Context Protocol (MCP) server that provides seamless integration with Lightcast APIs for job titles, skills analysis, and career data. Built with FastMCP and modern Python development practices.

## 🚀 Features

### Core APIs Implemented

- **🏷️ Titles API**: Job title search, normalization, and hierarchy analysis
- **🎯 Skills API**: Skills search, categorization, and extraction from text
- **📊 Classification API**: Map concepts to occupation codes (O*NET SOC)
- **🔗 Similarity API**: Find similar occupations and skills, occupation-to-skills mapping
- **⚡ Workflow API**: Combined title normalization and skills mapping

### Key Tools

- **`normalize_title_and_get_skills`**: Complete workflow that normalizes job titles → maps to occupations → retrieves associated skills
- **`get_title_skills_simple`**: Simplified version for quick skill extraction
- **`analyze_job_posting_skills`**: Comprehensive job posting analysis combining title and description
- **`search_job_titles`**: Search Lightcast's comprehensive job title database
- **`search_skills`**: Search and filter skills by category and type with advanced filters

## 🛠️ Installation

### Prerequisites

- Python 3.10+ (recommended: 3.12)
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Lightcast API credentials (Client ID and Secret)

### Quick Start with uv (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/mcp-lightcast.git
cd mcp-lightcast

# 2. Set up development environment 
make setup

# 3. Configure your API credentials
# Edit .env with your Lightcast API credentials

# 4. Validate configuration
make validate-config

# 5. Run the server
make run
```

### Alternative Installation Methods

<details>
<summary>📦 Using Docker (Production Ready)</summary>

```bash
# Pull the latest image
docker pull ghcr.io/your-org/mcp-lightcast:latest

# Run with environment file
docker run --rm -it --env-file .env ghcr.io/your-org/mcp-lightcast:latest

# Or with Docker Compose
docker-compose up
```

</details>

<details>
<summary>🐍 Using uvx (Isolated Execution)</summary>

```bash
# Run directly without installation
uvx --from mcp-lightcast mcp-lightcast --help

# Run with environment variables
LIGHTCAST_CLIENT_ID=xxx LIGHTCAST_CLIENT_SECRET=yyy uvx --from mcp-lightcast mcp-lightcast
```

</details>

<details>
<summary>📦 Using pip</summary>

```bash
# Install from PyPI
pip install mcp-lightcast

# Or install from source
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run the server
mcp-lightcast
```

</details>

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your Lightcast API credentials:

```bash
# Required - Lightcast API Configuration
LIGHTCAST_CLIENT_ID=your_client_id_here
LIGHTCAST_CLIENT_SECRET=your_client_secret_here

# Optional - API Configuration (with defaults)
LIGHTCAST_BASE_URL=https://api.lightcast.io
LIGHTCAST_OAUTH_URL=https://auth.lightcast.io/oauth/token
LIGHTCAST_RATE_LIMIT=1000

# Optional - MCP Server Configuration
MCP_SERVER_NAME=lightcast-mcp-server
LOG_LEVEL=INFO
MASK_ERROR_DETAILS=true
```

### Lightcast API Access

To use this server, you need:

1. 📝 A [Lightcast API account](https://docs.lightcast.dev/contact)
2. 🔑 Client ID and Client Secret for OAuth2 authentication
3. 🎯 Access to the following Lightcast APIs:
   - Titles API - Job title search and normalization
   - Skills API - Skills search and categorization
   - Classification API - Occupation code mapping
   - Similarity API - Skills and occupation relationships

Contact [Lightcast](https://docs.lightcast.dev/contact) for API access and credentials.

## 🎯 Usage

### Command Line Interface

The server includes a comprehensive CLI with multiple options:

```bash
# Basic usage
mcp-lightcast

# With custom log level
mcp-lightcast --log-level DEBUG

# Validate configuration without starting server
mcp-lightcast --validate-config

# Use custom environment file
mcp-lightcast --env-file /path/to/custom.env

# Quiet mode (no logging)
mcp-lightcast --quiet

# Show help
mcp-lightcast --help
```

### Development Commands

Using the included Makefile for easy development:

```bash
# Quick development setup and run
make dev

# Run with debug logging
make dev-server

# Run all quality checks
make check

# Run tests with coverage
make test-coverage

# Show Claude Desktop configuration
make claude-config
```

### Claude Desktop Integration

#### Using uv (Recommended)

```json
{
  "mcpServers": {
    "lightcast": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/mcp-lightcast",
        "mcp-lightcast"
      ],
      "env": {
        "LIGHTCAST_CLIENT_ID": "your_client_id",
        "LIGHTCAST_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

#### Using Docker

```json
{
  "mcpServers": {
    "lightcast": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "LIGHTCAST_CLIENT_ID",
        "-e", "LIGHTCAST_CLIENT_SECRET",
        "ghcr.io/your-org/mcp-lightcast:latest"
      ],
      "env": {
        "LIGHTCAST_CLIENT_ID": "your_client_id",
        "LIGHTCAST_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

#### Using uvx (Isolated)

```json
{
  "mcpServers": {
    "lightcast": {
      "command": "uvx",
      "args": [
        "--from",
        "mcp-lightcast",
        "mcp-lightcast"
      ],
      "env": {
        "LIGHTCAST_CLIENT_ID": "your_client_id",
        "LIGHTCAST_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Available Tools

#### Workflow Tools

**normalize_title_and_get_skills**
```python
# Complete workflow: normalize title → map to occupations → get skills
result = await normalize_title_and_get_skills(
    raw_title="sr software dev",
    max_occupations=5,
    max_skills_per_occupation=20,
    skill_type="Hard Skill",  # Optional: filter by skill type
    confidence_threshold=0.5,
    version="2023.4"
)
```

**get_title_skills_simple**
```python
# Simplified workflow for quick results
result = await get_title_skills_simple(
    raw_title="data scientist",
    limit=50,
    version="2023.4"
)
```

**analyze_job_posting_skills**
```python
# Analyze complete job posting
result = await analyze_job_posting_skills(
    job_title="Software Engineer",
    job_description="Full job description text...",
    extract_from_description=True,
    merge_results=True
)
```

#### Title Tools

**search_job_titles**
```python
# Search job titles
titles = await search_job_titles(
    query="software engineer",
    limit=10,
    offset=0
)
```

**normalize_job_title**
```python
# Normalize a raw job title
result = await normalize_job_title("sr software dev")
```

#### Skills Tools

**search_skills**
```python
# Search skills with filters
skills = await search_skills(
    query="python",
    skill_type="Hard Skill",
    category="Information Technology",
    limit=10
)
```

**extract_skills_from_text**
```python
# Extract skills from job description
skills = await extract_skills_from_text(
    text="Looking for Python developer with React experience...",
    confidence_threshold=0.5
)
```

### Example Workflows

#### 1. Analyze a Job Title for Required Skills

```python
# Get comprehensive skills for a job title
result = await normalize_title_and_get_skills("Machine Learning Engineer")

print(f"Normalized Title: {result['normalized_title']['name']}")
print(f"Confidence: {result['normalized_title']['confidence']}")
print(f"Related Occupations: {[occ['occupation_name'] for occ in result['occupation_mappings']]}")
print(f"Skills Found: {len(result['skills'])}")

for skill in result['skills'][:10]:  # Top 10 skills
    print(f"- {skill['name']} ({skill.get('type', 'Unknown')})")
```

#### 2. Compare Skills Requirements Across Job Titles

```python
# Compare different job titles
titles = ["Data Scientist", "Machine Learning Engineer", "Software Engineer"]
all_results = {}

for title in titles:
    result = await get_title_skills_simple(title, limit=30)
    all_results[title] = set(skill['name'] for skill in result['skills'])

# Find common skills
common_skills = set.intersection(*all_results.values())
print(f"Common skills across all roles: {common_skills}")
```

#### 3. Analyze Job Posting

```python
job_description = \"\"\"
We're looking for a Senior Software Engineer with expertise in Python, 
React, and cloud technologies. Experience with Docker, Kubernetes, 
and AWS is required. Strong communication skills and team collaboration 
abilities are essential.
\"\"\"

result = await analyze_job_posting_skills(
    job_title="Senior Software Engineer",
    job_description=job_description,
    extract_from_description=True,
    merge_results=True
)

print(f"Title-based skills: {len(result['title_based_skills'])}")
print(f"Description-extracted skills: {len(result['description_extracted_skills'])}")
print(f"Merged unique skills: {len(result['merged_skills'])}")
```

## 🧪 Development

### Prerequisites

- Python 3.10+ (recommended: 3.12)
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for containerized development)
- Make (for development commands)

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-org/mcp-lightcast.git
cd mcp-lightcast

# Quick setup (installs dependencies, creates .env)
make setup

# Install development dependencies only  
make install-dev

# Run development server with debug logging
make dev-server
```

### Project Structure

```
mcp-lightcast/
├── 📁 src/mcp_lightcast/           # Main package
│   ├── __init__.py                 # CLI entry point with Click
│   ├── __main__.py                 # Module execution entry
│   ├── server.py                   # FastMCP server instance
│   ├── 📁 auth/                    # Authentication modules
│   │   ├── __init__.py
│   │   └── oauth.py               # OAuth2 implementation
│   ├── 📁 apis/                    # API client modules  
│   │   ├── __init__.py
│   │   ├── base.py                # Base client with error handling
│   │   ├── titles.py              # Titles API client
│   │   ├── skills.py              # Skills API client
│   │   ├── classification.py      # Classification API client
│   │   └── similarity.py          # Similarity API client
│   ├── 📁 tools/                   # MCP tools registration
│   │   ├── __init__.py
│   │   ├── titles_tools.py        # Title-related MCP tools
│   │   ├── skills_tools.py        # Skills-related MCP tools
│   │   ├── workflow_tools.py      # Combined workflow tools
│   │   └── normalize_title_get_skills.py  # Core workflow logic
│   └── 📁 utils/                   # Utility functions
│       └── __init__.py
├── 📁 tests/                       # Test suite
│   ├── 📁 unit/                    # Unit tests
│   ├── 📁 integration/             # Integration tests
│   └── conftest.py                # Pytest fixtures
├── 📁 config/                      # Configuration management
│   └── settings.py                # Pydantic settings
├── 📁 .github/workflows/           # CI/CD pipelines
│   └── ci.yml                     # GitHub Actions workflow
├── 🐳 Dockerfile                   # Production container
├── 🐳 Dockerfile.dev               # Development container  
├── 🐳 docker-compose.yml           # Multi-service setup
├── 📋 Makefile                     # Development commands
├── 📦 pyproject.toml               # Project metadata & dependencies
├── 🔒 uv.lock                      # Dependency lock file
└── 📖 README.md                    # This file
```

### Development Workflow

#### Code Quality & Testing

```bash
# Run all quality checks (lint + type-check + test)
make check

# Individual quality checks
make lint           # Ruff linting
make type-check     # MyPy type checking  
make format         # Black + Ruff formatting

# Testing options
make test           # Run all tests
make test-coverage  # Tests with coverage report
make test-basic     # Basic functionality test
```

#### Docker Development

```bash
# Build Docker images
make docker-build       # Production image
make docker-build-dev   # Development image

# Run with Docker
make docker-run         # Run production container
make docker-dev         # Run development container

# Test Docker configuration
make docker-test        # Validate container setup
```

#### uv Package Management

```bash
# Dependency management
make uv-lock           # Generate lockfile
make uv-sync           # Sync from lockfile
make uv-update         # Update all dependencies

# Add dependencies
make uv-add PACKAGE=requests
make uv-add-dev PACKAGE=pytest-mock
```

## API Reference

### Rate Limits

- Default: 1000 requests per hour per API key
- Rate limit headers are included in responses
- Rate limit errors (429) are handled gracefully

### Error Handling

- Authentication errors are automatically retried
- Rate limits include reset time information
- API errors include detailed status codes and messages
- Network errors are handled with appropriate timeouts

### Supported API Versions

- Default: `2023.4`
- All tools accept a `version` parameter to use different API versions
- Newer versions may include additional features and updated data

## Future Enhancements

The following APIs are planned for future implementation:

- **Occupation Benchmark API**: Industry benchmarking and compensation data
- **Career Pathways API**: Career progression and pathway analysis
- **Job Postings API**: Real-time job market data and trends

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Lightcast API Documentation](https://docs.lightcast.dev/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

For issues and feature requests, please use the [GitHub Issues](https://github.com/your-org/mcp-lightcast/issues) page.