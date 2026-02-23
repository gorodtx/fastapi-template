#!/usr/bin/env sh
set -eu

template_path="/etc/alertmanager/alertmanager.yml"
rendered_path="/tmp/alertmanager.rendered.yml"
app_env="${APP_ENV:-dev}"
retention="${ALERTMANAGER_RETENTION:-120h}"
web_listen_address="${ALERTMANAGER_WEB_LISTEN_ADDRESS:-0.0.0.0:9093}"
cluster_listen_address="${ALERTMANAGER_CLUSTER_LISTEN_ADDRESS:-0.0.0.0:9094}"
cluster_peers="${ALERTMANAGER_CLUSTER_PEERS:-}"
cluster_advertise_address="${ALERTMANAGER_CLUSTER_ADVERTISE_ADDRESS:-}"

ticket_url="${ALERTMANAGER_WEBHOOK_TICKET_URL:-http://host.docker.internal:5001/alerts}"
page_url="${ALERTMANAGER_WEBHOOK_PAGE_URL:-$ticket_url}"
heartbeat_url="${ALERTMANAGER_WEBHOOK_HEARTBEAT_URL:-$ticket_url}"
ticket_slack_webhook_url="${ALERTMANAGER_TICKET_SLACK_WEBHOOK_URL:-}"
page_slack_webhook_url="${ALERTMANAGER_PAGE_SLACK_WEBHOOK_URL:-$ticket_slack_webhook_url}"
page_pagerduty_routing_key="${ALERTMANAGER_PAGE_PAGERDUTY_ROUTING_KEY:-}"

is_prod_env() {
  case "$app_env" in
    prod | PROD | production | PRODUCTION)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_local_receiver() {
  case "$1" in
    *"host.docker.internal"* | *"://127.0.0.1"* | *"://localhost"*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if is_prod_env; then
  if is_local_receiver "$ticket_url"; then
    echo "ALERTMANAGER_WEBHOOK_TICKET_URL points to local address in prod."
    exit 1
  fi
  if is_local_receiver "$page_url"; then
    echo "ALERTMANAGER_WEBHOOK_PAGE_URL points to local address in prod."
    exit 1
  fi
  if is_local_receiver "$heartbeat_url"; then
    echo "ALERTMANAGER_WEBHOOK_HEARTBEAT_URL points to local address in prod."
    exit 1
  fi
  if [ -n "$ticket_slack_webhook_url" ] && is_local_receiver "$ticket_slack_webhook_url"; then
    echo "ALERTMANAGER_TICKET_SLACK_WEBHOOK_URL points to local address in prod."
    exit 1
  fi
  if [ -n "$page_slack_webhook_url" ] && is_local_receiver "$page_slack_webhook_url"; then
    echo "ALERTMANAGER_PAGE_SLACK_WEBHOOK_URL points to local address in prod."
    exit 1
  fi
fi

escape_for_sed() {
  printf '%s' "$1" | sed -e 's/[\/&|]/\\&/g'
}

ticket_escaped="$(escape_for_sed "$ticket_url")"
page_escaped="$(escape_for_sed "$page_url")"
heartbeat_escaped="$(escape_for_sed "$heartbeat_url")"
cluster_peer_args=""
for peer in $(printf '%s' "$cluster_peers" | tr ',' ' '); do
  if [ -n "$peer" ]; then
    cluster_peer_args="${cluster_peer_args} --cluster.peer=${peer}"
  fi
done
cluster_advertise_arg=""
if [ -n "$cluster_advertise_address" ]; then
  cluster_advertise_arg="--cluster.advertise-address=${cluster_advertise_address}"
fi

sed \
  -e "s|__TICKET_WEBHOOK_URL__|$ticket_escaped|g" \
  -e "s|__PAGE_WEBHOOK_URL__|$page_escaped|g" \
  -e "s|__HEARTBEAT_WEBHOOK_URL__|$heartbeat_escaped|g" \
  "$template_path" > "$rendered_path.tmp"

ticket_slack_block=""
if [ -n "$ticket_slack_webhook_url" ]; then
  ticket_slack_block="$(cat <<EOF
    slack_configs:
      - api_url: "$ticket_slack_webhook_url"
        send_resolved: true
        title: '[{{ .Status | toUpper }}][ticket] {{ .CommonLabels.alertname }}'
        text: '{{ template "default.message" . }}'
EOF
)"
fi

page_slack_block=""
if [ -n "$page_slack_webhook_url" ]; then
  page_slack_block="$(cat <<EOF
    slack_configs:
      - api_url: "$page_slack_webhook_url"
        send_resolved: true
        title: '[{{ .Status | toUpper }}][page] {{ .CommonLabels.alertname }}'
        text: '{{ template "default.message" . }}'
EOF
)"
fi

page_pagerduty_block=""
if [ -n "$page_pagerduty_routing_key" ]; then
  page_pagerduty_block="$(cat <<EOF
    pagerduty_configs:
      - routing_key: "$page_pagerduty_routing_key"
        send_resolved: true
        severity: '{{ if eq .CommonLabels.severity "page" }}critical{{ else }}warning{{ end }}'
        description: '{{ .CommonLabels.alertname }}'
EOF
)"
fi

awk \
  -v ticket_slack_block="$ticket_slack_block" \
  -v page_slack_block="$page_slack_block" \
  -v page_pagerduty_block="$page_pagerduty_block" \
  '
  $0 == "__TICKET_SLACK_CONFIG__" {
    if (length(ticket_slack_block) > 0) print ticket_slack_block
    next
  }
  $0 == "__PAGE_SLACK_CONFIG__" {
    if (length(page_slack_block) > 0) print page_slack_block
    next
  }
  $0 == "__PAGE_PAGERDUTY_CONFIG__" {
    if (length(page_pagerduty_block) > 0) print page_pagerduty_block
    next
  }
  { print }
  ' \
  "$rendered_path.tmp" > "$rendered_path"

rm -f "$rendered_path.tmp"

exec /bin/alertmanager \
  --config.file="$rendered_path" \
  --web.listen-address="$web_listen_address" \
  --cluster.listen-address="$cluster_listen_address" \
  $cluster_advertise_arg \
  $cluster_peer_args \
  --storage.path=/alertmanager \
  --data.retention="$retention"
