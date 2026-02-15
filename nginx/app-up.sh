#!/usr/bin/env sh
set -eu

attempt=0
max_attempts=60
while [ "$attempt" -lt "$max_attempts" ]; do
  if [ -x .venv/bin/alembic ] && [ -x .venv/bin/python ] && .venv/bin/python -V >/dev/null 2>&1; then
    if .venv/bin/alembic upgrade head; then
      break
    fi
  elif uv run alembic upgrade head; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done

if [ "$attempt" -ge "$max_attempts" ]; then
  echo "Failed to apply migrations after retries."
  exit 1
fi

if [ -x .venv/bin/uvicorn ] && [ -x .venv/bin/python ] && .venv/bin/python -V >/dev/null 2>&1; then
  exec .venv/bin/uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000
fi

exec uv run uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000
