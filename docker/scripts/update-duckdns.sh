#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"
DUCKDNS_URL_BASE="${DUCKDNS_URL_BASE:-https://www.duckdns.org/update}"

log() {
  echo "[duckdns] $*"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1" >&2
    exit 1
  fi
}

read_env_value() {
  local key="$1"
  awk -F= -v k="$key" '$1 == k { sub($1 FS, ""); print; exit }' "$ENV_FILE"
}

strip_duckdns_suffix() {
  local value="$1"
  value="${value%.duckdns.org}"
  printf '%s' "$value"
}

main() {
  require_command curl
  require_command awk

  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: env file not found: $ENV_FILE" >&2
    exit 1
  fi

  local domain token response
  domain="$(read_env_value "DUCKDNS_DOMAIN")"
  token="$(read_env_value "DUCKDNS_TOKEN")"

  if [ -z "$domain" ] || [ -z "$token" ]; then
    echo "ERROR: DUCKDNS_DOMAIN and DUCKDNS_TOKEN must be set in $ENV_FILE" >&2
    exit 1
  fi

  domain="$(strip_duckdns_suffix "$domain")"
  response="$(curl -fsS "${DUCKDNS_URL_BASE}?domains=${domain}&token=${token}&verbose=true")"

  if ! printf '%s' "$response" | grep -q '^OK'; then
    echo "ERROR: DuckDNS update failed: $response" >&2
    exit 1
  fi

  log "DuckDNS updated for ${domain}.duckdns.org"
}

main "$@"
