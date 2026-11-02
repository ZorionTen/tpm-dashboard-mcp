# TPM Dashboard MCP Server

> An MCP server that lets any AI agent fetch Jira data and render a React sprint health dashboard on demand. The AI client is the UI. The tools are the product.

**Part 11 — AI Productivity Utility · Prototype (MVP)**

## Problem

Technical Program Managers waste time manually pulling sprint data from Jira into slide decks to show leadership a health snapshot. The data exists; the friction is retrieval and formatting. This MCP server removes both: ask your AI agent for a dashboard, get one in the browser in under 10 seconds.

## Architecture

```
User in OpenCode/Claude Desktop → "Generate a status dashboard from Jira"
       ↓
AI client calls MCP tools (stdio)
       ↓
tpm-dashboard-mcp (single executable)
  ├─ Tool 1: fetch_jira_data()    → HTTP GET → Mock Jira (localhost:8000)
  └─ Tool 2: generate_dashboard() → computes velocity → serves React app :5173 → opens browser
       ↓
React (Vite) dashboard: metrics cards + color-coded issue table
```

| Component | Tech | Run |
|---|---|---|
| Mock Jira API | Python + FastAPI | `tpm-dashboard-mcp mock-jira` (port 8000) |
| MCP server | Python + `mcp` SDK (stdio) | `tpm-dashboard-mcp mcp` |
| Frontend | Vite + React, plain CSS | embedded static build (port 5173) |

## Quick start (release binary — no Python/Node required)

1. Download `tpm-dashboard-mcp-*` for your OS from [Releases](../../releases).
2. Start the mock Jira: `./tpm-dashboard-mcp mock-jira`
3. Connect your AI client (see below) and ask: *"Fetch the latest Jira data and generate a dashboard."*
   Or test manually: `npx @modelcontextprotocol/inspector ./tpm-dashboard-mcp mcp`

## Connect to OpenCode

```json
{
  "mcp": {
    "tpm-dashboard": {
      "type": "local",
      "command": ["/absolute/path/tpm-dashboard-mcp", "mcp"],
      "enabled": true
    }
  }
}
```

Claude Desktop / Cursor: add the same command to their MCP config. Restart the client, then ask for a dashboard in natural language.

## Development setup (< 5 minutes)

```bash
git clone <repo> && cd tpm-dashboard-mcp
pip install -r requirements.txt          # mcp, fastapi, uvicorn
cd frontend && npm install && cd ..      # Vite + React

python main.py mock-jira                 # terminal 1 — mock Jira :8000
python main.py mcp                       # terminal 2 — MCP server (stdio)
```

In dev mode `generate_dashboard` writes `frontend/public/data.json` and starts the Vite dev server (port 5173). Build the frontend (`cd frontend && npm run build`) before packaging.

## Build the single executable yourself

```bash
cd frontend && npm install && npm run build && cd ..
pip install pyinstaller
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist:frontend" main.py
# Windows: --add-data "frontend/dist;frontend"
./dist/tpm-dashboard-mcp mock-jira   # or: ... mcp
```

Cross-platform binaries (Linux, Windows, macOS) are built automatically by GitHub Actions on every `v*` tag — see [`.github/workflows/release.yml`](.github/workflows/release.yml).

## The two tools

| Tool | Input | Output |
|---|---|---|
| `fetch_jira_data` | none | JSON of sprint issues (`key`, `summary`, `status`, `story_points`) from `GET /rest/api/3/search` |
| `generate_dashboard` | `jira_json` (string) | Computes total/done points + velocity %, writes the payload, serves the React dashboard at `http://localhost:5173`, opens the browser |

Dashboard shows: total points, done points, velocity %, issue count, completed issues, and a color-coded issue table (Done = green, In Progress = amber, Blocked = red). Invalid JSON produces a rendered error state instead of a crash.

## Project layout

```
mock_jira.py          FastAPI mock Jira (5 issues, port 8000)
mcp_server.py         FastMCP/MCPServer: two tools over stdio
main.py               CLI entry: mock-jira | mcp
frontend/             Vite + React app (MetricCard, IssueTable)
.github/workflows/    Release: PyInstaller on Linux/Windows/macOS
```

## Out of scope (future work)

- Real Jira auth (OAuth/API tokens) and live sync
- Persistence, multi-user, deployed hosting
- Scheduled/automatic report generation
- Slack/email delivery of the dashboard

## Video

Loom walkthrough: _link pending_

---

Prototype · built with Cursor/Claude Code + OpenCode · Part 11
