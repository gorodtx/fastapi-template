#!/usr/bin/env sh
set -eu

exec uv run --no-dev --no-sync --frozen alembic upgrade head
