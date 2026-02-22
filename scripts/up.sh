#!/usr/bin/env sh
set -eu

compose_file="${COMPOSE_FILE:-compose.yaml}"
hostnet_override_file="${HOSTNET_OVERRIDE_FILE:-compose.linux-hostnet.yaml}"
max_attempts="${MAX_ATTEMPTS:-45}"
compose_up_max_retries="${COMPOSE_UP_MAX_RETRIES:-3}"
auto_hostnet_fallback="${AUTO_HOSTNET_FALLBACK:-1}"
enable_observability="${ENABLE_OBSERVABILITY:-0}"
obs_profile_name="${OBS_PROFILE_NAME:-obs}"
core_services_default="postgres redis migrate app nginx"
obs_services_default="otel-collector prometheus grafana alertmanager loki alloy tempo"

if [ "$enable_observability" = "1" ]; then
  default_services="${core_services_default} ${obs_services_default}"
else
  default_services="${core_services_default}"
fi
services="${SERVICES:-$default_services}"
observability_requested=0
if [ "$enable_observability" = "1" ]; then
  observability_requested=1
fi
case " $services " in
  *" otel-collector "* | *" prometheus "* | *" grafana "* | *" alertmanager "* | *" loki "* | *" alloy "* | *" tempo "*)
    observability_requested=1
    ;;
esac

if [ -z "${OBS_OTEL_ENABLED:-}" ]; then
  if [ "$observability_requested" = "1" ]; then
    OBS_OTEL_ENABLED=true
  else
    OBS_OTEL_ENABLED=false
  fi
  export OBS_OTEL_ENABLED
fi

enforce_standard_port_env() {
  var_name="$1"
  required_value="$2"
  current_val="$(eval "printf '%s' \"\${${var_name}:-}\"")"
  if [ -n "$current_val" ] && [ "$current_val" != "$required_value" ]; then
    echo "Ignoring ${var_name}=${current_val}; enforcing standard port ${required_value}."
  fi
  eval "${var_name}=${required_value}"
  export "$var_name"
}

port_in_use() {
  port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -E "[:.]${port}$" >/dev/null 2>&1
    return $?
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

port_listener_pids() {
  port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp 2>/dev/null \
      | awk -v suffix=":${port}" '$4 ~ suffix"$" {print $0}' \
      | grep -o 'pid=[0-9]\+' \
      | cut -d= -f2 \
      | sort -u
    return 0
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u
    return 0
  fi
  return 0
}

stop_docker_publishers() {
  port="$1"
  if ! command -v docker >/dev/null 2>&1; then
    return 0
  fi
  container_ids="$(docker ps -q --filter "publish=$port" 2>/dev/null || true)"
  if [ -n "$container_ids" ]; then
    echo "Stopping Docker containers that occupy port $port..."
    docker stop $container_ids >/dev/null 2>&1 || true
  fi
}

signal_port_pids() {
  port="$1"
  signal_name="$2"
  pids="$(port_listener_pids "$port" || true)"
  if [ -z "$pids" ]; then
    return 0
  fi
  for pid in $pids; do
    if [ "$pid" = "$$" ]; then
      continue
    fi
    kill "-$signal_name" "$pid" >/dev/null 2>&1 || true
  done
}

free_port_or_fail() {
  port="$1"
  if ! port_in_use "$port"; then
    return 0
  fi

  echo "Port $port is occupied. Attempting to free it..."
  stop_docker_publishers "$port"

  if port_in_use "$port"; then
    signal_port_pids "$port" TERM
    sleep 1
  fi
  if port_in_use "$port"; then
    signal_port_pids "$port" KILL
    sleep 1
  fi
  if port_in_use "$port"; then
    echo "Failed to free required port $port."
    exit 1
  fi
  echo "Port $port is free."
}

free_required_ports() {
  required_ports="5432 6379 ${APP_HOST_PORT}"
  if [ "$observability_requested" = "1" ]; then
    required_ports="${required_ports} ${OBS_OTEL_GRPC_PORT} ${OBS_PROMETHEUS_PORT} ${OBS_GRAFANA_PORT} ${OBS_ALERTMANAGER_PORT} ${OBS_LOKI_PORT} ${OBS_ALLOY_PORT} ${OBS_TEMPO_HTTP_PORT}"
  fi
  for port in $required_ports; do
    free_port_or_fail "$port"
  done
}

down_current_project() {
  if [ "$observability_requested" = "1" ]; then
    docker compose -f "$compose_file" --profile "$obs_profile_name" down >/dev/null 2>&1 || true
    if [ -f "$hostnet_override_file" ]; then
      docker compose -f "$compose_file" -f "$hostnet_override_file" --profile "$obs_profile_name" down >/dev/null 2>&1 || true
    fi
    return 0
  fi

  docker compose -f "$compose_file" down >/dev/null 2>&1 || true
  if [ -f "$hostnet_override_file" ]; then
    docker compose -f "$compose_file" -f "$hostnet_override_file" down >/dev/null 2>&1 || true
  fi
}

stop_repo_compose_containers() {
  if ! command -v docker >/dev/null 2>&1; then
    return 0
  fi
  repo_workdir="$(pwd)"
  container_ids="$(docker ps -q --filter "label=com.docker.compose.project.working_dir=${repo_workdir}" 2>/dev/null || true)"
  if [ -n "$container_ids" ]; then
    echo "Stopping compose containers from this repository to free standard ports..."
    docker stop $container_ids >/dev/null 2>&1 || true
  fi
}

enforce_standard_port_env APP_HOST_PORT 8080
enforce_standard_port_env OBS_OTEL_GRPC_PORT 4317
enforce_standard_port_env OBS_PROMETHEUS_PORT 9090
enforce_standard_port_env OBS_GRAFANA_PORT 3000
enforce_standard_port_env OBS_ALERTMANAGER_PORT 9093
enforce_standard_port_env OBS_LOKI_PORT 3100
enforce_standard_port_env OBS_ALLOY_PORT 12345
enforce_standard_port_env OBS_TEMPO_HTTP_PORT 3200
down_current_project
stop_repo_compose_containers
free_required_ports

default_system_url="http://127.0.0.1:${APP_HOST_PORT}/system"
hostnet_system_url="http://127.0.0.1:8080/system"
default_prometheus_url="http://127.0.0.1:${OBS_PROMETHEUS_PORT}/-/ready"
default_grafana_url="http://127.0.0.1:${OBS_GRAFANA_PORT}/api/health"
default_alertmanager_url="http://127.0.0.1:${OBS_ALERTMANAGER_PORT}/-/ready"
default_loki_url="http://127.0.0.1:${OBS_LOKI_PORT}/ready"
default_alloy_url="http://127.0.0.1:${OBS_ALLOY_PORT}/"
default_tempo_url="http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}/ready"

http_ready() {
  target_url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --connect-timeout 2 --max-time 3 "$target_url" >/dev/null 2>&1
    return $?
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -T 3 -qO- "$target_url" >/dev/null 2>&1
    return $?
  fi
  echo "Neither curl nor wget is installed. Cannot probe $target_url."
  return 1
}

in_stack_http_ready() {
  if [ "$observability_requested" = "1" ]; then
    nginx_container_id="$(docker compose -f "$compose_file" --profile "$obs_profile_name" ps -q nginx 2>/dev/null || true)"
  else
    nginx_container_id="$(docker compose -f "$compose_file" ps -q nginx 2>/dev/null || true)"
  fi
  if [ -z "$nginx_container_id" ]; then
    return 1
  fi
  docker exec "$nginx_container_id" sh -lc "wget -T 3 -qO- http://127.0.0.1:8080/system >/dev/null 2>&1"
}

wait_system_ready() {
  target_url="$1"
  attempt=0
  while [ "$attempt" -lt "$max_attempts" ]; do
    if http_ready "$target_url"; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

wait_system_ready_in_stack() {
  attempt=0
  while [ "$attempt" -lt "$max_attempts" ]; do
    if in_stack_http_ready; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

obs_host_ready_once() {
  if [ "$observability_requested" != "1" ]; then
    return 0
  fi
  http_ready "$default_prometheus_url" \
    && http_ready "$default_grafana_url" \
    && http_ready "$default_alertmanager_url" \
    && http_ready "$default_loki_url" \
    && http_ready "$default_alloy_url" \
    && http_ready "$default_tempo_url"
}

wait_observability_ready() {
  if [ "$observability_requested" != "1" ]; then
    return 0
  fi
  attempt=0
  while [ "$attempt" -lt "$max_attempts" ]; do
    if obs_host_ready_once; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

up_default() {
  echo "Starting stack with default compose networking..."
  attempt=0
  if [ "$observability_requested" = "1" ]; then
    echo "Observability profile: enabled (${obs_profile_name})"
    echo "Using host ports: app=${APP_HOST_PORT}, otel-grpc=${OBS_OTEL_GRPC_PORT}, prometheus=${OBS_PROMETHEUS_PORT}, grafana=${OBS_GRAFANA_PORT}, alertmanager=${OBS_ALERTMANAGER_PORT}, loki=${OBS_LOKI_PORT}, alloy=${OBS_ALLOY_PORT}, tempo=${OBS_TEMPO_HTTP_PORT}"
    while [ "$attempt" -lt "$compose_up_max_retries" ]; do
      if DOCKER_BUILD_NETWORK="${DOCKER_BUILD_NETWORK:-default}" docker compose -f "$compose_file" --profile "$obs_profile_name" up -d --build $services; then
        return 0
      fi
      attempt=$((attempt + 1))
      if [ "$attempt" -lt "$compose_up_max_retries" ]; then
        echo "Default compose up failed; retrying (${attempt}/${compose_up_max_retries})..."
        sleep 2
      fi
    done
    return 1
  else
    echo "Observability profile: disabled (core only)"
    echo "Using host port: app=${APP_HOST_PORT}"
    while [ "$attempt" -lt "$compose_up_max_retries" ]; do
      if DOCKER_BUILD_NETWORK="${DOCKER_BUILD_NETWORK:-default}" docker compose -f "$compose_file" up -d --build $services; then
        return 0
      fi
      attempt=$((attempt + 1))
      if [ "$attempt" -lt "$compose_up_max_retries" ]; then
        echo "Default compose up failed; retrying (${attempt}/${compose_up_max_retries})..."
        sleep 2
      fi
    done
    return 1
  fi
}

up_hostnet() {
  echo "Starting stack with Linux host-network fallback..."
  attempt=0
  if [ "$observability_requested" = "1" ]; then
    while [ "$attempt" -lt "$compose_up_max_retries" ]; do
      if DOCKER_BUILD_NETWORK="${FALLBACK_DOCKER_BUILD_NETWORK:-host}" docker compose -f "$compose_file" -f "$hostnet_override_file" --profile "$obs_profile_name" up -d --build $services; then
        return 0
      fi
      attempt=$((attempt + 1))
      if [ "$attempt" -lt "$compose_up_max_retries" ]; then
        echo "Host-network compose up failed; retrying (${attempt}/${compose_up_max_retries})..."
        sleep 2
      fi
    done
    return 1
  else
    while [ "$attempt" -lt "$compose_up_max_retries" ]; do
      if DOCKER_BUILD_NETWORK="${FALLBACK_DOCKER_BUILD_NETWORK:-host}" docker compose -f "$compose_file" -f "$hostnet_override_file" up -d --build $services; then
        return 0
      fi
      attempt=$((attempt + 1))
      if [ "$attempt" -lt "$compose_up_max_retries" ]; then
        echo "Host-network compose up failed; retrying (${attempt}/${compose_up_max_retries})..."
        sleep 2
      fi
    done
    return 1
  fi
}

default_up_ok=1
default_in_stack_only=0
default_obs_unreachable=0
default_system_ready=0
if up_default; then
  if wait_system_ready "$default_system_url"; then
    default_system_ready=1
    if [ "$observability_requested" = "1" ] && ! wait_observability_ready; then
      echo "Observability endpoints are not host-reachable in default mode."
      if [ "$(uname -s)" = "Linux" ] && [ "$auto_hostnet_fallback" = "1" ] && [ -f "$hostnet_override_file" ]; then
        default_obs_unreachable=1
      else
        exit 1
      fi
    fi
  fi
  if [ "$default_obs_unreachable" = "0" ] && [ "$default_system_ready" -eq 1 ]; then
    echo "Stack is ready: $default_system_url"
    if [ "$observability_requested" = "1" ]; then
      echo "Prometheus: http://127.0.0.1:${OBS_PROMETHEUS_PORT}"
      echo "Grafana: http://127.0.0.1:${OBS_GRAFANA_PORT}"
      echo "Alertmanager: http://127.0.0.1:${OBS_ALERTMANAGER_PORT}"
      echo "Loki: http://127.0.0.1:${OBS_LOKI_PORT}"
      echo "Alloy: http://127.0.0.1:${OBS_ALLOY_PORT}"
      echo "Tempo: http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}"
    fi
    exit 0
  fi
  if [ "$default_obs_unreachable" = "0" ] && wait_system_ready_in_stack; then
    default_in_stack_only=1
    if [ "$(uname -s)" != "Linux" ] || [ "$auto_hostnet_fallback" != "1" ] || [ ! -f "$hostnet_override_file" ]; then
      echo "Stack is running internally, but host probe failed for $default_system_url."
      if [ "$observability_requested" = "1" ]; then
        echo "Prometheus: http://127.0.0.1:${OBS_PROMETHEUS_PORT}"
        echo "Grafana: http://127.0.0.1:${OBS_GRAFANA_PORT}"
        echo "Alertmanager: http://127.0.0.1:${OBS_ALERTMANAGER_PORT}"
        echo "Loki: http://127.0.0.1:${OBS_LOKI_PORT}"
        echo "Alloy: http://127.0.0.1:${OBS_ALLOY_PORT}"
        echo "Tempo: http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}"
      fi
      exit 0
    fi
  fi
else
  default_up_ok=0
fi

if [ "$(uname -s)" = "Linux" ] && [ "$auto_hostnet_fallback" = "1" ] && [ -f "$hostnet_override_file" ]; then
  if [ "$default_up_ok" -eq 0 ]; then
    echo "Default mode failed to start, switching to host-network fallback..."
  elif [ "$default_obs_unreachable" -eq 1 ]; then
    echo "Default mode app is ready, but observability endpoints are not reachable; switching to host-network fallback..."
  elif [ "$default_in_stack_only" -eq 1 ]; then
    echo "Default mode is only internally reachable, switching to host-network fallback..."
  else
    echo "Default mode is not reachable from host, switching to host-network fallback..."
  fi
  docker compose -f "$compose_file" down >/dev/null 2>&1 || true
  if up_hostnet; then
    if wait_system_ready "$hostnet_system_url"; then
      if [ "$observability_requested" = "1" ] && ! wait_observability_ready; then
        echo "Host-network fallback started, but observability endpoints are still not reachable from host."
        exit 1
      fi
      echo "Stack is ready with host-network fallback: $hostnet_system_url"
      if [ "$observability_requested" = "1" ]; then
        echo "Prometheus: http://127.0.0.1:${OBS_PROMETHEUS_PORT}"
        echo "Grafana: http://127.0.0.1:${OBS_GRAFANA_PORT}"
        echo "Alertmanager: http://127.0.0.1:${OBS_ALERTMANAGER_PORT}"
        echo "Loki: http://127.0.0.1:${OBS_LOKI_PORT}"
        echo "Alloy: http://127.0.0.1:${OBS_ALLOY_PORT}"
        echo "Tempo: http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}"
      fi
      exit 0
    fi
    if wait_system_ready_in_stack; then
      echo "Stack is running with host-network fallback, but host probe failed for $hostnet_system_url."
      if [ "$observability_requested" = "1" ]; then
        echo "Prometheus: http://127.0.0.1:${OBS_PROMETHEUS_PORT}"
        echo "Grafana: http://127.0.0.1:${OBS_GRAFANA_PORT}"
        echo "Alertmanager: http://127.0.0.1:${OBS_ALERTMANAGER_PORT}"
        echo "Loki: http://127.0.0.1:${OBS_LOKI_PORT}"
        echo "Alloy: http://127.0.0.1:${OBS_ALLOY_PORT}"
        echo "Tempo: http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}"
      fi
      exit 0
    fi
  fi
fi

echo "Failed to start a host-reachable stack. Last service status:"
docker compose -f "$compose_file" ps || true
exit 1
