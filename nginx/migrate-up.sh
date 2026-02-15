#!/usr/bin/env sh
set -eu

exec uv run alembic upgrade head
