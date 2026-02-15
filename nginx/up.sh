#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

wait_ready() {
  for _ in {1..60}; do
    if curl -fsS --max-time 2 "http://127.0.0.1:8080/openapi.json" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

docker compose up -d postgres redis migrate app nginx
if wait_ready; then
  echo "Stack is ready: http://127.0.0.1:8080/docs"
  exit 0
fi

echo "Services started, but API is not ready. Check logs:"
echo "  docker compose logs --tail=100 app"
echo "  docker compose logs --tail=100 nginx"
echo "  docker compose logs --tail=100 migrate"
exit 1
