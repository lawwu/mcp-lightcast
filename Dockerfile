FROM python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.14-slim AS production
WORKDIR /app
RUN useradd --create-home --uid 1001 appuser
COPY --from=build --chown=appuser:appuser /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 3000
ENTRYPOINT ["mcp-lightcast"]
CMD ["--transport", "stdio"]
