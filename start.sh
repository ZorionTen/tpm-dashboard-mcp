#!/usr/bin/env bash
# THE APP — one command starts everything the demo needs:
#   - mock Jira API   http://127.0.0.1:8000/rest/api/3/search
#   - dashboard UI    http://localhost:5173
# Leave this terminal running; Ctrl+C stops it all (or ./stop.sh).
#
# MCP is NOT run here — your AI client (Claude Desktop / OpenCode) spawns it
# itself on connect:  command = <executable> start
set -euo pipefail
cd "$(dirname "$0")"

if [ -x dist/tpm-dashboard-mcp ]; then
  exec dist/tpm-dashboard-mcp app "$@"
elif [ -x "$HOME/.local/bin/tpm-dashboard-mcp" ]; then
  exec "$HOME/.local/bin/tpm-dashboard-mcp" app "$@"
else
  # source checkout: needs `pip install -r requirements.txt` and a built frontend
  [ -d frontend/dist ] || { echo "[tpm-dashboard] frontend/dist missing — building..." >&2; (cd frontend && npm run build); }
  exec python3 main.py app "$@"
fi
