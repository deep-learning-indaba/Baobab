#!/usr/bin/env bash
# Starts a complete Baobab environment for agent runs and browser verification:
# Postgres, the storage emulator and the API in docker compose, migrations, seed
# data (`flask seed-agent`), the Vite dev server on the host, and Playwright.
#
# Used by .github/workflows/claude-agent.yml. It also runs locally next to an
# existing dev stack if you give it its own project name and ports:
#
#   COMPOSE_PROJECT_NAME=baobab-agent BAOBAB_DB_PORT=5433 BAOBAB_STORAGE_PORT=4444 \
#   BAOBAB_API_PORT=5001 BAOBAB_WEB_PORT=8090 BAOBAB_TEST_PASSWORD=... scripts/agent/start-env.sh
#
# Stop it with scripts/agent/stop-env.sh using the same variables.
set -euo pipefail

cd "$(dirname "$0")/../.."

: "${BAOBAB_TEST_PASSWORD:?Set BAOBAB_TEST_PASSWORD (the password given to every seeded account)}"
export BAOBAB_API_PORT="${BAOBAB_API_PORT:-5000}"
export BAOBAB_WEB_PORT="${BAOBAB_WEB_PORT:-8080}"
PW_DIR="${PW_DIR:-/tmp/pw_test}"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/tmp/pw_browsers}"
VITE_LOG="${VITE_LOG:-/tmp/baobab-vite-${BAOBAB_WEB_PORT}.log}"

if docker compose version >/dev/null 2>&1; then
  DC=(docker compose)
else
  DC=(docker-compose)
fi

log() { printf '\n==> %s\n' "$*"; }

wait_for() {
  local what=$1 tries=$2; shift 2
  for _ in $(seq "$tries"); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  echo "Timed out waiting for $what" >&2
  return 1
}

http_ok() { curl -s -o /dev/null --max-time 5 -w '%{http_code}' "$1" | grep -q '^[23]'; }

log "Starting db, storage and web"
"${DC[@]}" up -d --build db storage web
wait_for "Postgres" 60 "${DC[@]}" exec -T db pg_isready -U docker

log "Applying migrations"
"${DC[@]}" exec -T web sh -c "cd /code/api && flask db upgrade 2>&1" | tail -3

log "Seeding agent test data"
"${DC[@]}" exec -T -e BAOBAB_TEST_PASSWORD web sh -c "cd /code/api && flask seed-agent" | { grep -v '^postgres://' || true; }

# The API answers 404 for an unknown path once it is up; any HTTP response will do.
wait_for "the API on port $BAOBAB_API_PORT" 60 \
  sh -c "curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$BAOBAB_API_PORT/ | grep -qv '^000'"

log "Starting the Vite dev server on port $BAOBAB_WEB_PORT"
(
  cd webapp
  pnpm install --frozen-lockfile --reporter=silent
  REACT_APP_API_URL="http://localhost:$BAOBAB_API_PORT" \
    nohup pnpm exec vite --port "$BAOBAB_WEB_PORT" --strictPort >"$VITE_LOG" 2>&1 &
  echo $! >"$VITE_LOG.pid"
)
wait_for "Vite on port $BAOBAB_WEB_PORT (log: $VITE_LOG)" 90 http_ok "http://localhost:$BAOBAB_WEB_PORT/"

log "Installing Playwright in $PW_DIR"
mkdir -p "$PW_DIR"
if ! (cd "$PW_DIR" && node -e "require.resolve('playwright')") >/dev/null 2>&1; then
  rm -rf "$PW_DIR/node_modules/playwright" "$PW_DIR/node_modules/playwright-core"
  npm install --prefix "$PW_DIR" --no-save --silent playwright
fi
if [ "$(uname)" = "Linux" ]; then
  npx --prefix "$PW_DIR" playwright install --with-deps chromium
else
  npx --prefix "$PW_DIR" playwright install chromium
fi

log "Ready"
echo "  App:  http://localhost:$BAOBAB_WEB_PORT"
echo "  API:  http://localhost:$BAOBAB_API_PORT"
echo "  Seeded accounts use BAOBAB_TEST_PASSWORD; see api/app/utils/seed_agent.py for the list."
