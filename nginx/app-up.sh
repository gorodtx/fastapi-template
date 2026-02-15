#!/usr/bin/env sh
set -eu

exec uv run --no-dev --no-sync --frozen uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000
