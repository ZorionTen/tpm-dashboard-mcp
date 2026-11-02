#!/usr/bin/env bash
# One command to stop everything start.sh runs:
#   MCP server process, mock Jira (binary or source), Vite dev server.
#   (The embedded dashboard server lives inside the MCP process and dies with it.)
set -u
cd "$(dirname "$0")"

stopped=0
stop() { # $1 = pgrep/pkill pattern, $2 = label
  if pgrep -f "$1" >/dev/null 2>&1; then
    pkill -f "$1"
    echo "stopped: $2"
    stopped=1
  fi
}

stop 'tpm-dashboard-mcp($| (app|start|mcp|mock-jira))' 'MCP server / app / mock Jira (binary)'
stop 'main[.]py ($|app |start |mcp |mock-jira)'        'MCP server / app / mock Jira (source)'
stop 'node_modules/.bin/vite'                      'Vite dev server'

sleep 1
if [ "$stopped" -eq 0 ]; then
  echo "nothing to stop"
else
  echo "all stopped"
fi
