#!/usr/bin/env sh
set -eu

exec uv run uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000
