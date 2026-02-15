FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
RUN attempts=0; max_attempts=20; \
  until uv sync --frozen --no-dev --no-install-project; do \
    attempts=$((attempts + 1)); \
    if [ "$attempts" -ge "$max_attempts" ]; then \
      echo "uv sync failed after ${max_attempts} attempts"; \
      exit 1; \
    fi; \
    sleep 2; \
  done

COPY alembic.ini ./
COPY migrations ./migrations
COPY nginx ./nginx
COPY src ./src
