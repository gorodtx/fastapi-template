#!/usr/bin/env sh
set -eu

compose_file="${COMPOSE_FILE:-compose.yaml}"
hostnet_override_file="${HOSTNET_OVERRIDE_FILE:-compose.linux-hostnet.yaml}"
services="${SERVICES:-postgres redis migrate app nginx}"
system_url="${SYSTEM_URL:-http://127.0.0.1:8080/system}"
max_attempts="${MAX_ATTEMPTS:-45}"
auto_hostnet_fallback="${AUTO_HOSTNET_FALLBACK:-1}"

http_ready() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --connect-timeout 2 --max-time 3 "$system_url" >/dev/null 2>&1
    return $?
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -T 3 -qO- "$system_url" >/dev/null 2>&1
    return $?
  fi
  echo "Neither curl nor wget is installed. Cannot probe $system_url."
  return 1
}

wait_system_ready() {
  attempt=0
  while [ "$attempt" -lt "$max_attempts" ]; do
    if http_ready; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

up_default() {
  echo "Starting stack with default compose networking..."
  DOCKER_BUILD_NETWORK="${DOCKER_BUILD_NETWORK:-default}" docker compose -f "$compose_file" up -d --build $services
}

up_hostnet() {
  echo "Starting stack with Linux host-network fallback..."
  DOCKER_BUILD_NETWORK="${FALLBACK_DOCKER_BUILD_NETWORK:-host}" docker compose -f "$compose_file" -f "$hostnet_override_file" up -d --build $services
}

default_up_ok=1
if up_default; then
  if wait_system_ready; then
    echo "Stack is ready: $system_url"
    exit 0
  fi
else
  default_up_ok=0
fi

if [ "$(uname -s)" = "Linux" ] && [ "$auto_hostnet_fallback" = "1" ] && [ -f "$hostnet_override_file" ]; then
  if [ "$default_up_ok" -eq 0 ]; then
    echo "Default mode failed to start, switching to host-network fallback..."
  else
    echo "Default mode is not reachable from host, switching to host-network fallback..."
  fi
  docker compose -f "$compose_file" down >/dev/null 2>&1 || true
  if up_hostnet; then
    if wait_system_ready; then
      echo "Stack is ready with host-network fallback: $system_url"
      exit 0
    fi
  fi
fi

echo "Failed to start a host-reachable stack. Last service status:"
docker compose -f "$compose_file" ps || true
exit 1
