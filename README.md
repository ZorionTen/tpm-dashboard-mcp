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

| Component | Tech | Start |
|---|---|---|
| Mock Jira API | Python + FastAPI | `tpm-dashboard-mcp mock-jira` (port 8000) |
| MCP server | Python + `mcp` SDK v2 (stdio) | `tpm-dashboard-mcp mcp` (spawned by your AI client) |
| Frontend | Vite + React, plain CSS | served on port 5173 (embedded or Vite dev) |

---

## Quick start (release binary — no Python/Node needed)

**1. Download** the executable for your OS from the [Releases page](../../releases):

| OS | File |
|---|---|
| Linux x86_64 | `tpm-dashboard-mcp-linux-x86_64` |
| Windows x86_64 | `tpm-dashboard-mcp-windows-x86_64.exe` |
| macOS (Apple Silicon) | `tpm-dashboard-mcp-macos-arm64` |

```bash
# Linux / macOS — make it executable and put it on your PATH
chmod +x tpm-dashboard-mcp-*
sudo mv tpm-dashboard-mcp-* /usr/local/bin/tpm-dashboard-mcp   # optional

# macOS only: first run may be blocked by Gatekeeper
xattr -d com.apple.quarantine tpm-dashboard-mcp-macos-arm64
```

Windows: rename to `tpm-dashboard-mcp.exe` if you like, keep it anywhere.

**2. Start the mock Jira** (leave this terminal running):

```bash
tpm-dashboard-mcp mock-jira        # → http://127.0.0.1:8000/rest/api/3/search
```

Verify: `curl http://127.0.0.1:8000/rest/api/3/search`

**3. Connect your AI client** (see below), then ask it:

> *"Fetch the latest Jira data and generate a dashboard."*

Your browser opens `http://localhost:5173` with the sprint health dashboard.

**Try it without an AI client** (MCP Inspector):

```bash
npx @modelcontextprotocol/inspector tpm-dashboard-mcp mcp
# In the Inspector UI: run fetch_jira_data → copy output →
# run generate_dashboard with jira_json = that output
```

---

## Connect to OpenCode

Add the MCP server to `opencode.json` — global (`~/.config/opencode/opencode.json`) or per-project (`.opencode/opencode.json` / `opencode.json` in the repo):

```json
{
  "mcp": {
    "tpm-dashboard": {
      "type": "local",
      "command": ["/usr/local/bin/tpm-dashboard-mcp", "mcp"],
      "enabled": true
    }
  }
}
```

- Use the absolute path to the executable (`command` + `args: ["mcp"]` is equivalent).
- **Restart OpenCode** after saving.
- Make sure `tpm-dashboard-mcp mock-jira` is running in a terminal.
- Test: ask OpenCode *"Fetch the latest Jira data and generate a dashboard."*

## Connect to Claude Desktop

Edit Claude Desktop's config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- (Settings → Developer → "Edit Config" opens it)

```json
{
  "mcpServers": {
    "tpm-dashboard": {
      "command": "/usr/local/bin/tpm-dashboard-mcp",
      "args": ["mcp"]
    }
  }
}
```

- Windows: use the full path, e.g. `"C:\\Tools\\tpm-dashboard-mcp.exe"`.
- **Fully quit and reopen Claude Desktop.**
- Start the mock Jira first, then ask Claude for a dashboard. The 🔨/tools icon shows `tpm-dashboard` when connected.

Cursor and any other MCP client work the same way: command = the executable, args = `["mcp"]`, transport = stdio.

---

## Build and run from source (development)

Requires **Python 3.10+** and **Node 18+**.

```bash
git clone https://github.com/ZorionTen/tpm-dashboard-mcp.git
cd tpm-dashboard-mcp

pip install -r requirements.txt        # mcp, fastapi, uvicorn
cd frontend && npm install && cd ..    # Vite + React

python main.py mock-jira               # terminal 1 — mock Jira on :8000
python main.py mcp                     # terminal 2 — MCP server over stdio
```

Dev mode differs from release mode in one way: `generate_dashboard` writes `frontend/public/data.json` and starts the Vite dev server (`npm run dev`, port 5173) instead of using the embedded server. The React app is identical.

Useful commands:

```bash
cd frontend && npm run dev             # frontend only (hot reload)
cd frontend && npm run build           # production build → frontend/dist/
python -m py_compile mock_jira.py mcp_server.py main.py
```

## Build the single executable

```bash
cd frontend && npm install && npm run build && cd ..
pip install pyinstaller

# Linux / macOS
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist:frontend" main.py

# Windows (CMD) — note the semicolon
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist;frontend" main.py

./dist/tpm-dashboard-mcp mock-jira      # or: ... mcp
```

### Cross-platform release (CI)

GitHub Actions builds all three binaries on every `v*` tag ([`.github/workflows/release.yml`](.github/workflows/release.yml)):

```bash
git tag v0.2.0
git push origin main --tags
# → workflow builds Linux (ubuntu-22.04 for glibc compatibility), Windows, macOS
# → binaries attach automatically to a GitHub Release with generated notes
```

---

## The two tools

| Tool | Input | Output |
|---|---|---|
| `fetch_jira_data` | none | JSON of sprint issues (`key`, `summary`, `status`, `story_points`) from `GET /rest/api/3/search` |
| `generate_dashboard` | `jira_json` (string) — array of issues, or object with an `issues` array | Computes total/done points + velocity %, serves the React dashboard at `http://localhost:5173`, opens the browser |

Dashboard shows: total points, done points, velocity %, issue count, completed issues, and a color-coded issue table (Done = green, In Progress = amber, Blocked = red). Invalid JSON produces a rendered error state instead of a crash.

## Project layout

```
mock_jira.py                      FastAPI mock Jira (5 issues, port 8000)
mcp_server.py                     MCPServer: two tools over stdio + embedded static server
main.py                           CLI entry: mock-jira | mcp (used by dev and packaging)
frontend/                         Vite + React app (App → MetricCard, IssueTable)
.github/workflows/release.yml     Release: PyInstaller on Linux/Windows/macOS
REQ.MD                            Requirements document
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `fetch_jira_data` returns an error | Mock Jira isn't running → start `tpm-dashboard-mcp mock-jira` |
| Browser shows "frontend not built" (source mode) | Run `cd frontend && npm run build` |
| Dashboard page shows "No data yet" | Call `generate_dashboard` first — nothing is served until it runs |
| Port 5173 already in use | Stop the other process (`lsof -i :5173`) or kill a stale Vite dev server |
| MCP tools not visible in the client | Verify the config path is absolute, restart the client, check its MCP logs |
| Linux binary: `GLIBC_... not found` | Use the release asset built on ubuntu-22.04 (older distros: build from source) |

## Out of scope (future work)

- Real Jira auth (OAuth/API tokens) and live sync
- Persistence, multi-user, deployed hosting
- Scheduled/automatic report generation
- Slack/email delivery of the dashboard
- Code signing / notarization of release binaries

## Video

Loom walkthrough: _link pending_

---

Prototype · built with Cursor/Claude Code + OpenCode · Part 11
