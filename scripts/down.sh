#!/usr/bin/env sh
set -eu

compose_file="${COMPOSE_FILE:-compose.yaml}"
hostnet_override_file="${HOSTNET_OVERRIDE_FILE:-compose.linux-hostnet.yaml}"

if [ -f "$hostnet_override_file" ]; then
  docker compose -f "$compose_file" -f "$hostnet_override_file" down --remove-orphans || true
fi
docker compose -f "$compose_file" down --remove-orphans || true

echo "Stack is stopped."
