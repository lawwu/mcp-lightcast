# Multi-stage build for MCP Lightcast Server
# Based on MCP Atlassian best practices with uv package management

# Build stage
FROM python:3.12-alpine AS build

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies into virtual environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY . .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM python:3.12-alpine AS production

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    tzdata

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Set working directory
WORKDIR /app

# Copy virtual environment from build stage
COPY --from=build --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application code
COPY --from=build --chown=appuser:appgroup /app/src /app/src
COPY --from=build --chown=appuser:appgroup /app/config /app/config
COPY --from=build --chown=appuser:appgroup /app/pyproject.toml /app/

# Make sure the virtual environment is in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set Python path
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default environment variables
ENV LIGHTCAST_BASE_URL="https://api.lightcast.io" \
    LIGHTCAST_OAUTH_URL="https://auth.lightcast.io/oauth/token" \
    LIGHTCAST_RATE_LIMIT="1000" \
    MCP_SERVER_NAME="lightcast-mcp-server" \
    LOG_LEVEL="INFO" \
    MASK_ERROR_DETAILS="true"

# Expose port for HTTP transport (when implemented)
EXPOSE 9000

# Default command - run with stdio transport
ENTRYPOINT ["mcp-lightcast"]
CMD ["--log-level", "INFO"]