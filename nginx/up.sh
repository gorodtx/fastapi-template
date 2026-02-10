#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

docker compose up -d postgres redis app nginx

for _ in {1..60}; do
  if docker compose exec -T nginx wget -qO- "http://127.0.0.1:8080/openapi.json" >/dev/null 2>&1; then
    echo "Stack is ready: http://127.0.0.1:8080/docs"
    exit 0
  fi
  sleep 1
done

echo "Services started, but API is not ready yet. Check logs:"
echo "  docker compose logs --tail=100 app"
echo "  docker compose logs --tail=100 nginx"
exit 1
