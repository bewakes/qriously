#!/usr/bin/env bash
# Qriously local dev servers: API (Django/ASGI) + app (static files).
# `start`/`restart` apply migrations first, so schema changes never 500 the API.
# Usage: scripts/dev.sh {start|stop|restart|status|logs|migrate|setup|open}
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT/server"
APP_PORT="${APP_PORT:-8080}"
API_PORT="${API_PORT:-8000}"
VENV="$SERVER_DIR/.venv"
LOG_DIR="${TMPDIR:-/tmp}"
API_LOG="$LOG_DIR/qriously-api.log"
APP_LOG="$LOG_DIR/qriously-app.log"
CORS="${CORS_ALLOWED_ORIGINS:-http://localhost:${APP_PORT},http://127.0.0.1:${APP_PORT}}"
APP_URL="http://localhost:${APP_PORT}/app/index.html"

pids_on() { lsof -ti "tcp:$1" -sTCP:LISTEN 2>/dev/null || true; }

require_venv() {
  if [ ! -x "$VENV/bin/uvicorn" ]; then
    echo "error: $VENV/bin/uvicorn not found." >&2
    echo "  cd server && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt" >&2
    exit 1
  fi
}

migrate_db() {
  require_venv
  ( cd "$SERVER_DIR" && "$VENV/bin/python" manage.py migrate --noinput )
}

start_api() {
  local pids; pids="$(pids_on "$API_PORT")"
  if [ -n "$pids" ]; then echo "api :$API_PORT already running (pid $pids)"; return 0; fi
  migrate_db
  ( cd "$SERVER_DIR" && CORS_ALLOWED_ORIGINS="$CORS" nohup "$VENV/bin/uvicorn" \
      config.asgi:application --port "$API_PORT" </dev/null >"$API_LOG" 2>&1 & )
  echo "api :$API_PORT started -> $API_LOG"
}

start_app() {
  local pids; pids="$(pids_on "$APP_PORT")"
  if [ -n "$pids" ]; then echo "app :$APP_PORT already running (pid $pids)"; return 0; fi
  ( cd "$ROOT" && nohup python3 "$ROOT/scripts/serve.py" "$APP_PORT" "$ROOT" </dev/null >"$APP_LOG" 2>&1 & )
  echo "app :$APP_PORT started -> $APP_LOG"
}

wait_ready() {
  local i
  for i in $(seq 1 40); do
    if curl -sf "http://localhost:$API_PORT/health/ready" >/dev/null 2>&1; then return 0; fi
    sleep 0.25
  done
  echo "warning: api did not become ready; see $API_LOG" >&2
}

stop_one() {
  local name="$1" port="$2" pids
  pids="$(pids_on "$port")"
  if [ -z "$pids" ]; then echo "$name :$port not running"; return 0; fi
  kill $pids 2>/dev/null || true
  for _ in $(seq 1 20); do [ -z "$(pids_on "$port")" ] && break; sleep 0.1; done
  pids="$(pids_on "$port")"
  if [ -n "$pids" ]; then kill -9 $pids 2>/dev/null || true; fi
  echo "$name :$port stopped"
}

status() {
  local api app
  api="$(pids_on "$API_PORT")"
  app="$(pids_on "$APP_PORT")"
  printf "api :%s  %s\n" "$API_PORT" "$([ -n "$api" ] && echo "running (pid $api)" || echo stopped)"
  printf "app :%s  %s\n" "$APP_PORT" "$([ -n "$app" ] && echo "running (pid $app)" || echo stopped)"
  printf "url : %s\n" "$APP_URL"
  printf "mock: %s?demo=1\n" "$APP_URL"
}

case "${1:-}" in
  start) start_api; start_app; wait_ready; status ;;
  stop) stop_one api "$API_PORT"; stop_one app "$APP_PORT" ;;
  restart) stop_one api "$API_PORT"; stop_one app "$APP_PORT"; start_api; start_app; wait_ready; status ;;
  status) status ;;
  logs) tail -n 50 "$API_LOG" "$APP_LOG" 2>/dev/null || true ;;
  migrate) migrate_db ;;
  setup) migrate_db; ( cd "$SERVER_DIR" && "$VENV/bin/python" manage.py seed_content ) ;;
  open) if command -v open >/dev/null; then open "$APP_URL"; else echo "$APP_URL"; fi ;;
  *) echo "usage: $0 {start|stop|restart|status|logs|migrate|setup|open}"; exit 1 ;;
esac
