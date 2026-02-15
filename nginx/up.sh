#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE_FILE="$ROOT_DIR/.tmp/compose_mode"

cd "$ROOT_DIR"

mkdir -p "$(dirname "$MODE_FILE")"

wait_ready() {
  for _ in {1..60}; do
    if curl -fsS --max-time 2 "http://127.0.0.1:8080/openapi.json" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

start_bridge() {
  docker compose up -d postgres redis app nginx
}

start_hostnet() {
  docker compose -f compose.yaml -f compose.hostnet.yaml up -d postgres redis app nginx
}

start_bridge
if wait_ready; then
  echo "bridge" > "$MODE_FILE"
  echo "Stack is ready (bridge): http://127.0.0.1:8080/docs"
  exit 0
fi

echo "Bridge publish path is not reachable from host; switching to hostnet fallback..."
docker compose down --remove-orphans
start_hostnet
if wait_ready; then
  echo "hostnet" > "$MODE_FILE"
  echo "Stack is ready (hostnet): http://127.0.0.1:8080/docs"
  exit 0
fi

echo "Services started, but API is not ready in bridge or hostnet mode. Check logs:"
echo "  docker compose logs --tail=100 app"
echo "  docker compose logs --tail=100 nginx"
echo "  docker compose -f compose.yaml -f compose.hostnet.yaml logs --tail=100 app"
echo "  docker compose -f compose.yaml -f compose.hostnet.yaml logs --tail=100 nginx"
exit 1
