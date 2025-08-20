# Makefile for MCP Lightcast development

.PHONY: help install install-dev test lint format clean docker-build docker-run docker-dev validate-config run dev-server

# Default target
help: ## Show this help message
	@echo "MCP Lightcast Development Commands"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies with uv
	uv sync --no-dev

install-dev: ## Install all dependencies including dev dependencies
	uv sync --all-groups

# Development
dev-server: ## Run development server with debug logging
	uv run mcp-lightcast --log-level DEBUG

run: ## Run the MCP server with default settings (streamable-http)
	uv run mcp-lightcast

run-stdio: ## Run the MCP server with stdio transport
	uv run mcp-lightcast --transport stdio

run-http: ## Run the MCP server with streamable-http transport on port 3000
	uv run mcp-lightcast --transport streamable-http --port 3000

validate-config: ## Validate configuration and authentication
	uv run mcp-lightcast --validate-config

# Testing
test: ## Run tests with pytest
	uv run pytest

test-verbose: ## Run tests with verbose output
	uv run pytest -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term

test-basic: ## Run basic functionality test
	uv run python test_basic_functionality.py

# Code Quality
lint: ## Run linting with ruff
	uv run ruff check src/ tests/

lint-fix: ## Run linting with auto-fix
	uv run ruff check --fix src/ tests/

format: ## Format code with black and ruff
	uv run black src/ tests/ config/
	uv run ruff format src/ tests/

type-check: ## Run type checking with mypy
	uv run mypy src/

quality: lint type-check ## Run all code quality checks

# Docker
docker-build: ## Build production Docker image
	docker build -t mcp-lightcast:latest .

docker-build-dev: ## Build development Docker image
	docker build -f Dockerfile.dev -t mcp-lightcast:dev .

docker-run: ## Run Docker container with environment file
	docker run --rm -it --env-file .env mcp-lightcast:latest

docker-dev: ## Run development Docker container
	docker-compose --profile dev up mcp-lightcast-dev

docker-test: ## Test Docker container configuration
	docker run --rm --env-file .env mcp-lightcast:latest --validate-config --quiet

# UV Commands
uv-lock: ## Generate uv.lock file
	uv lock

uv-sync: ## Sync dependencies from lock file
	uv sync --frozen

uv-update: ## Update all dependencies
	uv lock --upgrade

uv-add: ## Add a new dependency (usage: make uv-add PACKAGE=package_name)
	uv add $(PACKAGE)

uv-add-dev: ## Add a new dev dependency (usage: make uv-add-dev PACKAGE=package_name)
	uv add --dev $(PACKAGE)

# Cleaning
clean: ## Clean up build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

clean-docker: ## Clean up Docker images and containers
	docker-compose down
	docker image prune -f
	docker container prune -f

# Project Setup
setup: ## Initial project setup
	@echo "Setting up MCP Lightcast development environment..."
	uv sync --all-groups
	@echo "✅ Dependencies installed"
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env file from example"; fi
	@echo "🚀 Setup complete! Edit .env with your Lightcast API credentials."

setup-hooks: ## Install pre-commit hooks
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

# Git
git-hooks: setup-hooks ## Alias for setup-hooks

# Release
version: ## Show current version
	uv run python -c "from importlib.metadata import version; print(f'mcp-lightcast v{version(\"mcp-lightcast\")}')"

# Documentation
docs-serve: ## Serve documentation locally (if implemented)
	@echo "Documentation server not yet implemented"

# Claude Desktop Integration
claude-config: ## Show Claude Desktop configuration
	@echo "Add this to your Claude Desktop configuration:"
	@echo "{"
	@echo '  "mcpServers": {'
	@echo '    "lightcast": {'
	@echo '      "command": "uv",'
	@echo '      "args": ['
	@echo '        "run",'
	@echo '        "--directory",'
	@echo '        "$(PWD)",'
	@echo '        "mcp-lightcast"'
	@echo '      ],'
	@echo '      "env": {'
	@echo '        "LIGHTCAST_CLIENT_ID": "your_client_id",'
	@echo '        "LIGHTCAST_CLIENT_SECRET": "your_client_secret"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo "}"

# All-in-one commands
check: lint type-check test ## Run all checks (lint, type-check, test)

ci: clean install-dev check ## Run CI pipeline locally

dev: install-dev dev-server ## Quick development setup and run