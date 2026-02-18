#!/usr/bin/env sh
set -eu

compose_file="${COMPOSE_FILE:-compose.yaml}"
compose_override="${COMPOSE_OVERRIDE:-}"
base_url="${E2E_BASE_URL:-http://127.0.0.1:8080}"
max_attempts="${MAX_ATTEMPTS:-30}"

if [ -n "$compose_override" ]; then
  docker compose -f "$compose_file" -f "$compose_override" restart nginx >/dev/null
else
  docker compose -f "$compose_file" restart nginx >/dev/null
fi

attempt=0
while [ "$attempt" -lt "$max_attempts" ]; do
  if curl -fsS "$base_url/system" >/dev/null 2>&1; then
    echo "nginx pre-step: ready ($base_url/system)"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 1
done

echo "nginx pre-step: service not ready after ${max_attempts}s: $base_url/system"
exit 1
