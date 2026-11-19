#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export AIRLOCK_LOCAL_TOKEN="${AIRLOCK_LOCAL_TOKEN:-dev-local-token}"
mkdir -p "$ROOT/data"

echo "Start backend, dashboard, and demo-chat in separate terminals:"
echo "  make api"
echo "  make dashboard"
echo "  make demo-chat"
echo "Extension: cd apps/extension && npm run build, then load unpacked in Chrome"