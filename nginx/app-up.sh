#!/usr/bin/env sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found; installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

attempt=0
max_attempts=60
while [ "$attempt" -lt "$max_attempts" ]; do
  if uv run alembic upgrade head; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done

if [ "$attempt" -ge "$max_attempts" ]; then
  echo "Failed to apply migrations after retries."
  exit 1
fi

exec uv run uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000
