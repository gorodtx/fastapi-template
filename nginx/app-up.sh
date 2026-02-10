#!/usr/bin/env sh
set -eu

attempt=0
max_attempts=60
while [ "$attempt" -lt "$max_attempts" ]; do
  if /home/den/template/.venv/bin/alembic upgrade head; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done

if [ "$attempt" -ge "$max_attempts" ]; then
  echo "Failed to apply migrations after retries."
  exit 1
fi

exec /home/den/template/.venv/bin/uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000
