#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PLUGIN_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
SERVICE_BIN="$PLUGIN_ROOT/service/hanauta-mail-service"
if [ ! -x "$SERVICE_BIN" ]; then
  bash "$PLUGIN_ROOT/service/build.sh"
fi
nohup "$SERVICE_BIN" "${1:-90}" >/dev/null 2>&1 &
echo $! > "${XDG_RUNTIME_DIR:-/tmp}/hanauta-mail-service.pid"
echo "hanauta-mail-service started"
