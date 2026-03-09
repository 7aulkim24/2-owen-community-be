#!/usr/bin/env bash

set -euo pipefail

SERVICE_NAME="community-duckdns-refresh.service"
TIMER_NAME="community-duckdns-refresh.timer"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
TIMER_PATH="/etc/systemd/system/${TIMER_NAME}"

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 1
fi

DEPLOY_DIR="${1:-}"
if [ -z "$DEPLOY_DIR" ]; then
  echo "Usage: sudo $0 <deploy-dir>"
  echo "Example: sudo $0 /home/ubuntu/community"
  exit 1
fi

SCRIPT_PATH="${DEPLOY_DIR%/}/scripts/update-duckdns.sh"

if [ ! -x "$SCRIPT_PATH" ]; then
  echo "ERROR: executable script not found: $SCRIPT_PATH" >&2
  echo "Run: chmod +x ${SCRIPT_PATH}" >&2
  exit 1
fi

cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Update DuckDNS for community deployment
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=${SCRIPT_PATH}
WorkingDirectory=${DEPLOY_DIR}
EOF

cat > "$TIMER_PATH" <<EOF
[Unit]
Description=Run community DuckDNS refresh every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=${SERVICE_NAME}

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable "$TIMER_NAME"

echo "Installed: $SERVICE_PATH"
echo "Installed: $TIMER_PATH"
echo "Run now: sudo systemctl start ${SERVICE_NAME}"
echo "Enable timer: sudo systemctl start ${TIMER_NAME}"
