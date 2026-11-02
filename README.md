# TPM Dashboard MCP Server

> An MCP server that lets any AI agent fetch Jira data and render a React sprint health dashboard on demand. The AI client is the UI. The tools are the product.

**Part 11 — AI Productivity Utility · Prototype (MVP)**

## Problem

Technical Program Managers waste time manually pulling sprint data from Jira into slide decks to show leadership a health snapshot. The data exists; the friction is retrieval and formatting. This MCP server removes both: ask your AI agent for a dashboard, get one in the browser in under 10 seconds.

## The flow

```
1. User starts THE APP                ./start.sh
      → mock Jira API   http://127.0.0.1:8000/rest/api/3/search
      → dashboard UI    http://localhost:5173      (stays running; Ctrl+C stops it)

2. User starts Claude / OpenCode      (config: command = <executable> start)
      → client spawns the MCP server over stdio → "MCP connects"
      → attaches to the running app (if you skipped step 1, it auto-starts it)

3. User asks: "Fetch Jira and generate a dashboard"
      → agent calls fetch_jira_data → JSON
      → agent calls generate_dashboard → payload handed to the app
      → browser opens http://localhost:5173, agent replies with the URL + "Done."
```

```
User ── ./start.sh ──▶ APP PROCESS ── mock Jira :8000 ──▶ React dashboard :5173
                          ▲                                    ▲
AI client ── spawns ── MCP server (stdio) ── fetch / generate ─┘ (shared payload file)
```

| Piece | Runs in | Started by |
|---|---|---|
| App: mock Jira `:8000` + dashboard `:5173` | one foreground process | you — `./start.sh` |
| MCP server (4 tools, stdio) | child process | your AI client (Claude/OpenCode/Cursor) |
| React dashboard | inside the app process | the app |

The UI is the Google Stitch project **"Project Manager UI Dashboard"** ported to **React + MUI (Material UI)** — two pages: the dark dashboard and the light print-ready PDF layout (`#/pdf`). Payload hand-over file: `~/.cache/tpm-dashboard/dashboard_data.json` (the MCP tool writes it, the app serves it at `/data.json`).

---

## Quick start (release binary — no Python/Node needed)

**1. Download** the executable for your OS from the [Releases page](../../releases):

| OS | File |
|---|---|
| Linux x86_64 | `tpm-dashboard-mcp-linux-x86_64` |
| Windows x86_64 | `tpm-dashboard-mcp-windows-x86_64.exe` |
| macOS (Apple Silicon) | `tpm-dashboard-mcp-macos-arm64` |

```bash
chmod +x tpm-dashboard-mcp-*                        # Linux/macOS
xattr -d com.apple.quarantine tpm-dashboard-mcp-macos-arm64   # macOS Gatekeeper only
```

**2. Start the app** (leave this terminal running):

```bash
./start.sh
# [tpm-dashboard] TPM Dashboard app
# [tpm-dashboard] Connect AI client : /path/tpm-dashboard-mcp start   (stdio MCP)
# [tpm-dashboard] Mock Jira API : starting → http://127.0.0.1:8000/rest/api/3/search
# [tpm-dashboard] Dashboard UI  : starting → http://localhost:5173
# [tpm-dashboard] ready ...
```

**3. Connect your AI client** (see below), then ask:

> *"Fetch the latest Jira data and generate a dashboard."*

The agent calls the tools, your browser opens `http://localhost:5173`, and it replies with the URL and "Done." It can also produce the PDF report: `update_pdf` → `download_pdf`.

**Try it without an AI client** (MCP Inspector):

```bash
npx @modelcontextprotocol/inspector tpm-dashboard-mcp start
# run fetch_jira_data → copy output → run generate_dashboard with jira_json = that output
```

## Connect to OpenCode

Add to `opencode.json` — global (`~/.config/opencode/opencode.json` or `opencode.jsonc`) or project-level (`opencode.json` in the repo root):

```json
{
  "mcp": {
    "tpm-dashboard": {
      "type": "local",
      "command": ["/usr/local/bin/tpm-dashboard-mcp", "start"],
      "enabled": true
    }
  }
}
```

- `command` is the full invocation: absolute path + the `start` subcommand (connects to the app; auto-starts it if step 1 was skipped).
- **Restart OpenCode** after saving.
- Test: ask *"Fetch the latest Jira data and generate a dashboard."*

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
      "args": ["start"]
    }
  }
}
```

- Windows: full path, e.g. `"C:\\Tools\\tpm-dashboard-mcp.exe"`.
- **Fully quit and reopen Claude Desktop**, start the app (`./start.sh`), then ask for a dashboard. The 🔨 icon shows `tpm-dashboard` when connected.

Cursor and any other MCP client work the same way: command = the executable, args = `["start"]`, transport = stdio.

---

## Build and run from source (development)

Requires **Python 3.10+** and **Node 18+**.

```bash
git clone https://github.com/ZorionTen/tpm-dashboard-mcp.git
cd tpm-dashboard-mcp
pip install -r requirements.txt        # mcp, fastapi, uvicorn, playwright
python -m playwright install chromium  # browser for the update_pdf tool (once)
cd frontend && npm install && npm run build && cd ..   # one-time frontend build

./start.sh                             # the app (or: python main.py app)
```

All subcommands (also `python main.py <cmd>` from source):

| Command | What it does |
|---|---|
| `app` | the app — mock Jira + dashboard server, foreground (used by `start.sh`) |
| `start` | MCP stdio for AI clients — attaches to the app, auto-starts it if down (default) |
| `mcp` | MCP stdio only — never starts anything |
| `mock-jira` | standalone mock Jira on `:8000` |

After changing React code: `cd frontend && npm run build`, restart the app. (For hot reload during pure frontend work you can still use `npm run dev` on `:5173`, but the app is the supported way to serve data.)

## Build the single executable

```bash
cd frontend && npm install && npm run build && cd ..
pip install pyinstaller

# Linux / macOS
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist:frontend" main.py
# Windows (CMD) — note the semicolon
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist;frontend" main.py
```

**`dist/tpm-dashboard-mcp` is a single executable file** (~46 MB ELF on Linux, `.exe` on Windows) — Python interpreter, all modules, every pip dependency, and the built React frontend packed inside by PyInstaller. No Python or Node needed to run it:

```bash
./dist/tpm-dashboard-mcp app       # the app, from one file
```

### Cross-platform release (CI)

GitHub Actions builds all three binaries on every `v*` tag ([`.github/workflows/release.yml`](.github/workflows/release.yml)):

```bash
git tag v0.2.0 && git push origin main --tags
# → Linux (ubuntu-22.04 for glibc compatibility), Windows, macOS → attached to a GitHub Release
```

---

## Logging & `--debug`

Everything logs to **stderr** (stdout belongs to the MCP protocol).

The **app** prints its addresses on start (see Quick start above) plus the payload file path and Ctrl+C hint. The **MCP server** prints a banner:

```
[tpm-dashboard] MCP transport : stdio (no port/URL — your AI client spawns this process)
[tpm-dashboard] Mock Jira API : http://127.0.0.1:8000/rest/api/3/search
[tpm-dashboard] Dashboard UI  : http://localhost:5173 (from ./start.sh — the app)
[tpm-dashboard] logging       : stderr only; normal (use --debug for verbose)
[tpm-dashboard] Dashboard     : ready → http://localhost:5173  (velocity 44.8%)
```

**`--debug` adds verbose logging:** HTTP requests/responses, payload metrics (issues/points/velocity), app auto-start with pid and readiness timing, browser-open result, and every HTTP request the app serves:

```bash
./start.sh --debug                 # flags are forwarded to the executable
dist/tpm-dashboard-mcp --debug app
python main.py --debug app
```

To debug the MCP connection, add the flag to your client config:

```json
"command": ["/path/tpm-dashboard-mcp", "--debug", "start"]
```

(The client's MCP logs then show the server's stderr — OpenCode MCP logs, Claude Desktop → `~/Library/Logs/Claude/mcp*.log` on macOS.)

## Stopping

- **Ctrl+C in the `./start.sh` terminal** stops the app — both servers die together (they're one process).
- The MCP server handles Ctrl+C/SIGTERM too, and terminates any app *it* auto-started.
- To stop everything including strays:

```bash
./stop.sh     # MCP server, app, mock Jira (binary or source)
```

## The four tools

| Tool | Input | Output |
|---|---|---|
| `fetch_jira_data` | none | JSON of sprint issues (`key`, `summary`, `status`, `story_points`) from `GET /rest/api/3/search`; auto-starts the app if it's down |
| `generate_dashboard` | `jira_json` (string — issue array, or object with `issues` + narrative fields), `open_browser` (bool, default `true`), `milestone_status` / `risks_mitigations` / `key_wins` (strings, optional) | computes metrics, writes the payload for the app, returns the URL + summary ("…velocity 44.8%, 5 issues. Done.") |
| `update_pdf` | none | headless Chromium renders the `#/pdf` layout with the latest data → `~/.cache/tpm-dashboard/sprint-health-report.pdf` (+ path/size) |
| `download_pdf` | none | JSON: `path`, `size_bytes`, `modified`, `mime_type` of the current PDF — agent flow: **`update_pdf` → `download_pdf`** |

Dashboard shows: metric cards, Milestone Status, Risks & Mitigations (severity chips), Key Wins, and a color-coded issue table (Done = green, In Progress = amber, Blocked = red). Invalid JSON produces a rendered error state instead of a crash.

## Dashboard controls (agreed behaviors)

| Control | Behavior |
|---|---|
| **Export PDF** | navigates to the `#/pdf` report page, then opens the browser print dialog (also: floating *Print / Save PDF* strip on that page) |
| **Log Risk** | modal form → appends a `Blocked` row to the table (session-local; auto-assigned key, points count toward totals) |
| **Sync (refresh)** | re-fetches `/data.json` (latest generated payload) + toast |
| **Sprint selector** | static label — "Sprint 24 (Current)" |
| **Ticket links / open icons** | open `https://jira.example.com/browse/<KEY>` in a new tab (placeholder host) |
| **Theme toggle** | dark ⇄ light + toast; filter chips + search filter the table client-side |

## PDF report

- **In the browser:** *Export PDF* → the print-ready report page → print dialog (or the page's *Print / Save PDF* button).
- **From your agent:** ask *"update and download the PDF"* → agent calls `update_pdf` (fresh render from latest data) then `download_pdf` (gets the file path).
- Prerequisite for `update_pdf`: Playwright Chromium once per machine — `npx playwright install chromium` (browser lives outside the executable in `~/.cache/ms-playwright`).

## Project layout

```
mock_jira.py                      FastAPI mock Jira — 4 sprint datasets, one random per request (port 8000)
dashboard.py                      the app runtime: dashboard server (:5173), payload file, app lifecycle
mcp_server.py                     MCPServer: two tools over stdio
main.py                           CLI entry: app | start | mcp | mock-jira
frontend/                         Vite + React + MUI app — DashboardPage, PdfPage, IssueTable, AddBlockerDialog, KpiCard (Stitch design port)
start.sh                          one command → the app (binary → ~/.local/bin → source fallback)
stop.sh                           one command → stop everything
dist/tpm-dashboard-mcp            the single executable file (gitignored — built via PyInstaller/CI)
.github/workflows/release.yml     Release: PyInstaller on Linux/Windows/macOS
REQ.MD                            Requirements document
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser: `connection refused` on `:5173` | App not running → `./start.sh`, then ask the agent to generate again |
| Dashboard says "no data yet" | `generate_dashboard` hasn't run in this session → ask the agent once |
| `fetch_jira_data` returns an error | App's mock Jira down → `./start.sh` (the tool also retries after auto-start) |
| "frontend not built" | `cd frontend && npm run build`, restart the app |
| Port already in use | `./stop.sh` then start fresh |
| MCP tools not visible in the client | Absolute path in config, restart the client, check its MCP logs |
| `update_pdf` fails with missing Chromium | `npx playwright install chromium` (browser is installed once, outside the executable) |
| Linux binary: `GLIBC_... not found` | Use the release asset (ubuntu-22.04 build) or build from source |

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
