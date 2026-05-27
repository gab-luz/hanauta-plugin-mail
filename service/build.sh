#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
OUT="$SCRIPT_DIR/hanauta-mail-service"
cc -O2 -Wall -Wextra "$SCRIPT_DIR/hanauta-mail-service.c" -o "$OUT" $(pkg-config --cflags --libs glib-2.0)
echo "Built: $OUT"
