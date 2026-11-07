#!/usr/bin/env bash
# Stops what scripts/agent/start-env.sh started. Pass the same COMPOSE_PROJECT_NAME
# and BAOBAB_WEB_PORT. Add --volumes to also delete the database.
set -euo pipefail

cd "$(dirname "$0")/../.."

BAOBAB_WEB_PORT="${BAOBAB_WEB_PORT:-8080}"
VITE_LOG="${VITE_LOG:-/tmp/baobab-vite-${BAOBAB_WEB_PORT}.log}"

if [ -f "$VITE_LOG.pid" ]; then
  kill "$(cat "$VITE_LOG.pid")" 2>/dev/null || true
  rm -f "$VITE_LOG.pid"
fi
# pnpm starts vite as a child process, which can outlive the pnpm pid above.
pkill -f "vite --port $BAOBAB_WEB_PORT" 2>/dev/null || true

if [ "${COMPOSE_PROJECT_NAME:-}" = "" ] || [ "${COMPOSE_PROJECT_NAME}" = "baobab" ]; then
  echo "Refusing to stop the default compose project; set COMPOSE_PROJECT_NAME to the agent project." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  DC=(docker compose)
else
  DC=(docker-compose)
fi

if [ "${1:-}" = "--volumes" ]; then
  "${DC[@]}" down --volumes
else
  "${DC[@]}" down
fi
