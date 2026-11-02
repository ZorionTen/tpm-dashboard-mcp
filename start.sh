#!/usr/bin/env bash
# One command to start everything:
#   - mock Jira on :8000 (auto-started, detached)
#   - MCP server on stdio (blocks — this is what an AI client attaches to)
#
# Usage:
#   ./start.sh                     # manual / test
#   point your MCP client here:    ["<path>/start.sh"]
set -euo pipefail
cd "$(dirname "$0")"

if [ -x dist/tpm-dashboard-mcp ]; then
  exec dist/tpm-dashboard-mcp start
elif [ -x "$HOME/.local/bin/tpm-dashboard-mcp" ]; then
  exec "$HOME/.local/bin/tpm-dashboard-mcp" start
else
  # source checkout: needs pip install -r requirements.txt (and npm for dev frontend)
  exec python3 main.py start
fi
