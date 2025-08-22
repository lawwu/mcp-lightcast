# MCP Lightcast Server

[![PyPI Version](https://img.shields.io/pypi/v/mcp-lightcast)](https://pypi.org/project/mcp-lightcast/)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI/CD Pipeline](https://github.com/lawwu/mcp-lightcast/workflows/Release/badge.svg)](https://github.com/lawwu/mcp-lightcast/actions)

A production-ready Model Context Protocol (MCP) server that provides seamless integration with Lightcast APIs for job titles, skills analysis, and career data. Built with FastMCP and modern Python development practices.

**🎯 Current Status: v0.2.1**

## 🚀 Features

### ✅ **Working APIs & Endpoints**

#### **🎯 Skills API (9/9 endpoints)** - Version 9.33, 41,139 skills
- ✅ **Skills Search** - Search with filters (type, category, subcategory)
- ✅ **Individual Skill Retrieval** - Get detailed skill information by ID
- ✅ **Skills Extraction from Text** - Extract skills from job descriptions with confidence scores
- ✅ **Bulk Skills Retrieval** - Efficient batch processing of multiple skills
- ✅ **Related Skills** - Find skills related to a specific skill (POST endpoint working)
- ✅ **Similar Skills** - Find similar skills via Similarity API
- ✅ **Skill Types** - Get all available skill types
- ✅ **Version Metadata** - Complete API version and statistics information
- ✅ **Skills Metadata** - General skills taxonomy information

#### **🏷️ Titles API (8/8 endpoints)** - Version 5.47, 73,993 titles
- ✅ **Job Title Search** - Search Lightcast's comprehensive job title database
- ✅ **Individual Title Retrieval** - Get detailed title information by ID
- ✅ **Bulk Title Retrieval** - Efficient batch processing of multiple titles
- ✅ **Title Normalization** - Normalize raw job titles
- ✅ **Title Hierarchy** - Get hierarchical structure for titles
- ✅ **Version Metadata** - Complete API version and statistics information
- ✅ **General Metadata** - Latest version and attribution information
- ✅ **Full Metadata** - Comprehensive taxonomy information

#### **🔄 Classification API (5/5 endpoints)** - Version 2025.8
- ✅ **Skills Extraction** - Extract skills from text using classification models
- ✅ **Available Versions** - Get all available API versions
- ✅ **Version Metadata** - Detailed version information
- ✅ **Skill Normalization** - Normalize skill text via extraction
- ✅ **Title Normalization** - Normalize title text with fallback

#### **🔗 Similarity API (7/7 endpoints)** - Premium Features
- ✅ **Available Models** - Get all similarity models
- ✅ **API Metadata** - Similarity API capabilities
- ✅ **Occupation Skills** - Skills associated with occupations
- ✅ **Similar Occupations** - Find similar occupations
- ✅ **Similar Skills** - Find similar skills
- ✅ **SOC Model** - Direct SOC similarity queries
- ✅ **Skill Model** - Direct skill similarity queries

#### **📊 Occupation Benchmark API (6/6 endpoints)** - Premium Features
- ✅ **API Metadata** - Benchmark API capabilities
- ✅ **Available Areas** - Geographic areas available
- ✅ **Available Metrics** - All available benchmark metrics
- ✅ **Benchmark Data** - Salary and employment data
- ✅ **SOC Dimension** - SOC code dimension data
- ✅ **LOT Dimension** - LOT occupation dimension data

#### **🛤️ Career Pathways API (3/3 endpoints)** - Premium Features
- ✅ **API Metadata** - Career pathways capabilities
- ✅ **Available Dimensions** - Pathway analysis dimensions
- ✅ **Pathway Analysis** - Career transition analysis

#### **💼 Job Postings API (3/3 endpoints)** - Premium Features
- ✅ **Available Facets** - Job posting search facets
- ✅ **Postings Summary** - Job posting trends and statistics
- ✅ **Top Skills** - Most in-demand skills from job postings

#### **🔄 Workflow Integration (2/2 endpoints)** - Custom Workflows
- ✅ **Title → Skills Workflow** - Complete title normalization and skills extraction
- ✅ **Simple Title Skills** - Streamlined title-to-skills pipeline

### 🔧 **Core Functionality - All Working**
- **🎯 Skills Extraction from Text** - High accuracy skill identification from job descriptions
- **📊 Search & Discovery** - Fast, filtered search across skills, titles, and job postings
- **⚡ Bulk Operations** - Efficient processing of multiple items in single requests
- **🔄 Version Management** - Uses "latest" keyword with backward compatibility
- **🔐 OAuth2 Authentication** - Secure authentication with dynamic scope switching
- **🔗 Related & Similar Skills** - Find skills relationships via multiple APIs
- **💼 Job Market Data** - Real-time job posting analysis and trends
- **📊 Benchmarks & Analytics** - Salary and employment data access
- **🛤️ Career Pathways** - Career transition analysis and recommendations

### ✅ **Premium Features - All Working**
- ✅ **Title Normalization** - Working with premium authentication scope
- ✅ **Skills Classification** - Working via Classification API
- ✅ **Related Skills** - Working with corrected POST endpoint
- ✅ **Similarity Analysis** - Full access to similarity models
- ✅ **Job Market Analytics** - Real-time posting data and insights
- ✅ **Occupation Benchmarks** - Comprehensive salary and employment data

### 🛠️ **MCP Tools Available (23 core tools across 7 categories)**

#### **Skills Tools (7 tools)**
API Docs: https://docs.lightcast.dev/apis/skills

- `bulk_retrieve_skills` - Efficient bulk skill retrieval
- `extract_skills_from_text` - Extract skills with custom confidence threshold
- `find_similar_skills` - Find similar skills via Similarity API
- `get_skill_details` - Get detailed skill information by ID
- `get_skills_metadata` - General skills taxonomy metadata
- `get_related_skills` - Find skills related to a specific skill (now working with POST endpoint)
- `search_skills` - Search skills with advanced filters (type, category, subcategory)

#### **Titles Tools (4 tools)**
API Docs: https://docs.lightcast.dev/apis/titles

- `bulk_retrieve_titles` - Efficient bulk title retrieval
- `get_job_title_details` - Get detailed title information by ID
- `normalize_job_title` - Normalize raw job titles
- `search_job_titles` - Search job titles in Lightcast database

#### **Job Postings Tools (3 tools)**
API Docs: https://docs.lightcast.dev/apis/job-postings

- `get_job_posting_details` - Get detailed job posting information
- `get_posting_statistics` - Job posting trends and analytics
- `search_job_postings` - Search real-time job market data

#### **Classification Tools (1 tool)**
API Docs: https://docs.lightcast.dev/apis/classification

- `get_classification_metadata` - Classification API capabilities and metadata

#### **Occupation Benchmark Tools (2 tools)**
API Docs: https://docs.lightcast.dev/apis/occupation-benchmark

- `get_benchmark_metadata` - Benchmark API capabilities and metadata
- `get_occupation_benchmark` - Salary and employment benchmarks by occupation

#### **Similarity Tools (3 tools)**
API Docs: https://docs.lightcast.dev/apis/similarity

- `get_similarity_metadata` - Similarity API capabilities and metadata
- `get_pathways_metadata` - Career pathways API capabilities and metadata


#### **Unified Workflows (4 tools)** - ✅ Complete Pipelines
- `analyze_job_posting_skills` - Comprehensive job posting analysis
- `normalize_title_and_get_skills` - Complete title→skills workflow
- `normalize_title_and_extract_skills` - Alternative classification-based extraction


## 🛠️ Installation

### Prerequisites

- Python 3.12+ (required for uv-dynamic-versioning)
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Lightcast API credentials (Client ID and Secret with `emsi_open` scope). You can request free API access [here](https://lightcast.io/open-skills/access) which will give you access to the skills and titles taxonomies (subset of only the Skills and Titles APIs).

### 🚀 Quick Start with uvx (Recommended)

```bash
# Install and run directly from PyPI (no installation required)
uvx --from mcp-lightcast mcp-lightcast --help

# Run with environment variables
LIGHTCAST_CLIENT_ID=your_id LIGHTCAST_CLIENT_SECRET=your_secret \
uvx --from mcp-lightcast mcp-lightcast

# Use stdio transport for Claude Desktop
LIGHTCAST_CLIENT_ID=your_id LIGHTCAST_CLIENT_SECRET=your_secret \
uvx --from mcp-lightcast mcp-lightcast --transport stdio
```

### 📦 Install from PyPI

```bash
# Install globally
pip install mcp-lightcast

# Or with uv
uv tool install mcp-lightcast

# Run the server
mcp-lightcast --help
```

### 🔧 Development Installation

```bash
# 1. Clone the repository
git clone https://github.com/lawwu/mcp-lightcast.git
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

### 🐳 Docker Installation

```bash
# Pull the latest image (when available)
docker pull ghcr.io/lawwu/mcp-lightcast:latest

# Run with environment variables
docker run --rm -it \
  -e LIGHTCAST_CLIENT_ID=your_id \
  -e LIGHTCAST_CLIENT_SECRET=your_secret \
  ghcr.io/lawwu/mcp-lightcast:latest

# Or with environment file
docker run --rm -it --env-file .env ghcr.io/lawwu/mcp-lightcast:latest
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your Lightcast API credentials:

```bash
# Required - Lightcast API Configuration
LIGHTCAST_CLIENT_ID=your_client_id_here
LIGHTCAST_CLIENT_SECRET=your_client_secret_here

# Optional - API Configuration (with defaults)
LIGHTCAST_BASE_URL=https://api.lightcast.io
LIGHTCAST_OAUTH_URL=https://auth.emsicloud.com/connect/token
LIGHTCAST_OAUTH_SCOPE=emsi_open
LIGHTCAST_RATE_LIMIT=1000

# Optional - MCP Server Configuration
MCP_SERVER_NAME=lightcast-mcp-server
LOG_LEVEL=INFO
MASK_ERROR_DETAILS=true
```

### Lightcast API Access

To use this server, you need:

1. 📝 A [Lightcast API account](https://lightcast.io/open-skills/access)
2. 🔑 Client ID and Client Secret for OAuth2 authentication
3. 🎯 Access to the following Lightcast APIs:
   - Titles API - Job title search and normalization
   - Skills API - Skills search and categorization
   - Classification API - Occupation code mapping
   - Similarity API - Skills and occupation relationships


## 🎯 Usage

### Command Line Interface

The server includes a comprehensive CLI with multiple options:

```bash
# Basic usage (uses streamable-http on port 3000 by default)
mcp-lightcast

# Use stdio transport (for Claude Desktop integration)
mcp-lightcast --transport stdio

# Use streamable-http transport with custom port
mcp-lightcast --transport streamable-http --port 8080

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
        "ghcr.io/lawwu/mcp-lightcast:latest"
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

### 🔧 Detailed Tool Usage Examples

#### **🎯 Skills Tools**

**search_skills** - Search skills with advanced filters
```python
skills = await search_skills(
    query="python programming",
    limit=10,
    skill_type="Hard Skill",  # Optional: filter by skill type
    category="Information Technology",  # Optional: filter by category
    version="latest"  # Uses latest API version
)
```

**extract_skills_from_text** - Extract skills from job descriptions
```python
# Extract skills with custom confidence threshold
skills = await extract_skills_from_text(
    text="Looking for Python developer with React and database experience...",
    confidence_threshold=0.7,
    version="latest"
)
```

**extract_skills_simple** - Extract skills with default settings
```python
# Quick skills extraction with default confidence (0.5)
skills = await extract_skills_simple(
    text="We need Java developers with Spring Boot experience",
    version="latest"
)
```

**bulk_retrieve_skills** - Efficient bulk skill retrieval
```python
# Get multiple skills in one request
skills = await bulk_retrieve_skills(
    skill_ids=["KS125LS6N7WP4S6SFTCK", "KS440C66FGP5WGWYMP0F"],
    version="latest"
)
```

#### **🏷️ Titles Tools**

**search_job_titles** - Search job titles
```python
titles = await search_job_titles(
    query="software engineer",
    limit=10,
    version="latest"
)
```

**get_job_title_details** - Get detailed title information
```python
title = await get_job_title_details(
    title_id="ET6850661D6AE5FA86",
    version="latest"
)
```

**bulk_retrieve_titles** - Efficient bulk title retrieval
```python
titles = await bulk_retrieve_titles(
    title_ids=["ET6850661D6AE5FA86", "ETBF8AE9187B3810C5"],
    version="latest"
)
```

#### **📊 Metadata Tools**

**get_skills_version_metadata** - API version information
```python
metadata = await get_skills_version_metadata(version="latest")
# Returns: version, skill_count, language_support, skill_types, etc.
```

**get_titles_version_metadata** - API version information  
```python
metadata = await get_titles_version_metadata(version="latest")
# Returns: version, title_count, removed_title_count, fields
```

#### **⚠️ Limited Availability Tools**
Some tools require premium authentication scopes or have endpoint limitations:

**normalize_job_title** - ❌ Requires premium scope
```python
# Currently returns 401 Unauthorized with emsi_open scope
result = await normalize_job_title("sr software dev")
```

**analyze_job_posting_skills** - ✅ Working via skills extraction
```python
# Uses skills extraction instead of normalization
result = await analyze_job_posting_skills(
    job_title="Software Engineer",
    job_description="Full job description text...",
    extract_from_description=True  # Uses working skills extraction
)
```

### 🎯 Example Workflows

#### **1. Extract Skills from Job Description**

```python
# Analyze a job posting to extract relevant skills
job_description = """
We're looking for a Senior Software Engineer with expertise in Python, 
React, and cloud technologies. Experience with Docker, Kubernetes, 
and AWS is required. Strong communication skills and team collaboration 
abilities are essential.
"""

# Extract skills with high confidence
skills = await extract_skills_from_text(
    text=job_description,
    confidence_threshold=0.8,
    version="latest"
)

print(f"High-confidence skills found: {len(skills)}")
for skill in skills:
    print(f"- {skill['name']} (confidence: {skill['confidence']:.2f})")
```

#### **2. Compare Skills Across Job Titles**

```python
# Search and compare skills requirements for different roles
titles = ["Data Scientist", "Machine Learning Engineer", "Software Engineer"]
title_skills = {}

for title in titles:
    # Search for the title
    title_results = await search_job_titles(query=title, limit=1)
    if title_results:
        title_id = title_results[0]['id']
        
        # Get detailed title information  
        title_details = await get_job_title_details(title_id)
        title_skills[title] = title_details
        
print("Job title comparison completed")
```

#### **3. Bulk Skills Analysis**

```python
# Efficiently analyze multiple skills at once
skill_names = ["Python", "JavaScript", "Machine Learning", "Docker"]

# First search for skill IDs
skill_ids = []
for name in skill_names:
    results = await search_skills(query=name, limit=1)
    if results:
        skill_ids.append(results[0]['id'])

# Get detailed information for all skills in one request
if skill_ids:
    detailed_skills = await bulk_retrieve_skills(skill_ids)
    
    for skill in detailed_skills:
        print(f"Skill: {skill['name']}")
        print(f"Type: {skill.get('type', {}).get('name', 'Unknown')}")
        print(f"Category: {skill.get('category', 'Unknown')}")
        print("---")
```

#### **4. API Version and Statistics**

```python
# Get comprehensive API information
skills_meta = await get_skills_version_metadata()
titles_meta = await get_titles_version_metadata()

print(f"Skills API v{skills_meta['version']}: {skills_meta['skill_count']:,} skills")
print(f"Languages: {', '.join(skills_meta['language_support'])}")
print(f"Skill types: {len(skills_meta['skill_types'])}")

print(f"Titles API v{titles_meta['version']}: {titles_meta['title_count']:,} titles")
```

## 🧪 Development

### Prerequisites

- Python 3.12+ (required)
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for containerized development)
- Make (for development commands)

### Development Setup

```bash
# Clone and setup
git clone https://github.com/lawwu/mcp-lightcast.git
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

### API Version Flexibility

The MCP server provides flexible version management:

- **Default**: `"latest"` - Always uses the newest available API version
- **Backward Compatible**: Users can specify any previous version (e.g., `"5.47"`, `"9.33"`)
- **Future-Proof**: Automatically gets new API features when Lightcast releases updates

**Examples:**
```python
# Use latest version (default)
search_job_titles("software engineer")

# Use specific version for consistency
search_job_titles("software engineer", version="5.47")

# Use older version if needed
search_skills("python", version="9.32")
```

**Current API Versions:**
- Skills API: `9.33` with 41,139 skills (English, Spanish, French support)
- Titles API: `5.47` with 73,993 titles
- Both APIs use `"latest"` keyword for automatic version management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation & Support

### **API Documentation**
- [Lightcast API Documentation](https://docs.lightcast.dev/) - Official Lightcast API reference
- [FastMCP Documentation](https://gofastmcp.com/) - FastMCP framework documentation  
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification

### **Project Resources**
- [PyPI Package](https://pypi.org/project/mcp-lightcast/) - Official Python package
- [GitHub Repository](https://github.com/lawwu/mcp-lightcast) - Source code and issues
- [GitHub Releases](https://github.com/lawwu/mcp-lightcast/releases) - Version history and changelog

### **Getting Help**
- **Issues**: [GitHub Issues](https://github.com/lawwu/mcp-lightcast/issues) for bugs and feature requests
- **Discussions**: [GitHub Discussions](https://github.com/lawwu/mcp-lightcast/discussions) for questions and community support
- **Lightcast Support**: [Contact Lightcast](https://docs.lightcast.dev/contact) for API access and credentials

### **Current Status**
- **Version**: 0.2.0 (Production Ready)
- **API Coverage**: 43/43 endpoints (100%)
- **MCP Tools**: 23 core tools (streamlined)
- **Premium Features**: All working with user credentials
- **Python**: 3.12+ required
- **License**: MIT