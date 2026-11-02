# TPM Dashboard MCP Server

> An MCP server that lets any AI agent fetch Jira data and render a React sprint health dashboard on demand. The AI client is the UI. The tools are the product.

**AI Productivity Utility · Prototype (MVP)**

> **⚠️ Prototype — not a production application.** Mock Jira data, no authentication, no persistence, no database, no deployment, no SLAs. It demonstrates the concept end-to-end and nothing more.

## Problem

Technical Program Managers waste time manually pulling sprint data from Jira into slide decks to show leadership a health snapshot. The data exists; the friction is retrieval and formatting. This MCP server removes both: ask your AI agent for a dashboard, get one in the browser in under 10 seconds.

## The flow

```
1. User starts THE APP                tpm-dashboard-mcp app     (one command, no build)
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
User ── tpm-dashboard-mcp app ──▶ APP PROCESS ── mock Jira :8000 ──▶ React dashboard :5173
                                      ▲                                ▲
AI client ── spawns ── MCP server (stdio) ── fetch / generate ────────┘ (shared payload file)
```

| Piece | Runs in | Started by |
|---|---|---|
| App: mock Jira `:8000` + dashboard `:5173` | one foreground process | you — `tpm-dashboard-mcp app` (`./start.sh` only in a source checkout) |
| MCP server (4 tools, stdio) | child process | your AI client (Claude/OpenCode/Cursor) |
| React dashboard | inside the app process | the app |

The UI is the Google Stitch project **"Project Manager UI Dashboard"** ported to **React + MUI (Material UI)** — two pages: the dark dashboard and the light print-ready PDF layout (`#/pdf`). Payload hand-over file: `~/.cache/tpm-dashboard/dashboard_data.json` (the MCP tool writes it, the app serves it at `/data.json`).

---

## Quick start — run it without building

The [Releases page](../../releases/latest) ships **one executable per OS** (Linux, Windows, macOS) — no Python or Node needed to run it (Node is only optional, for the PDF tools and Inspector, noted below). No clone, **no `start.sh`** (that script only exists for source checkouts).

**1. Download** the executable for your OS from the [latest release](../../releases/latest), **2. install it to a fixed path** (the client configs below use `/usr/local/bin`):

| OS | File | Install |
|---|---|---|
| Linux x86_64 | `tpm-dashboard-mcp-linux-x86_64` | see below |
| Windows x86_64 | `tpm-dashboard-mcp-windows-x86_64.exe` | see below — runs as-is |
| macOS (Apple Silicon) | `tpm-dashboard-mcp-macos-arm64` | see below |
| macOS (Intel) | — no binary | [build from source](#build-and-run-from-source-development) |

**2. Install it to a fixed path** (the client configs below use `/usr/local/bin`):

Run these **in the directory you downloaded to** (e.g. `~/Downloads`):

```bash
# Linux
sudo install -m 755 tpm-dashboard-mcp-linux-x86_64 /usr/local/bin/tpm-dashboard-mcp

# macOS (Apple Silicon): clear Gatekeeper (skip the xattr line if it errors
# with "No such xattr" — the file has no quarantine attribute), then install
xattr -d com.apple.quarantine tpm-dashboard-mcp-macos-arm64 || true
sudo install -m 755 tpm-dashboard-mcp-macos-arm64 /usr/local/bin/tpm-dashboard-mcp
```

```powershell
# Windows: the .exe runs as-is (no chmod). Keep it somewhere permanent,
# e.g. C:\Tools — optionally add that folder to PATH:
move tpm-dashboard-mcp-windows-x86_64.exe C:\Tools\tpm-dashboard-mcp.exe
```

No PATH? Use the file's full path wherever this README says `/usr/local/bin/tpm-dashboard-mcp`.

**3. Start the app** — one command, leave the terminal running:

```bash
tpm-dashboard-mcp app
# [tpm-dashboard] TPM Dashboard app
# [tpm-dashboard] Connect AI client : /usr/local/bin/tpm-dashboard-mcp start   (stdio MCP)
# [tpm-dashboard] Mock Jira API : starting → http://127.0.0.1:8000/rest/api/3/search
# [tpm-dashboard] Dashboard UI  : starting → http://localhost:5173
# [tpm-dashboard] ready ...
```

Windows: `C:\Tools\tpm-dashboard-mcp.exe app`. **Ctrl+C stops everything** (both servers live in this one process).

**4. One-time, only if you want the PDF tools** (`update_pdf`/`download_pdf`) — requires Node:

```bash
npx playwright install chromium
```

**5. Connect your AI client** (see below), then ask:

> *"Fetch the latest Jira data and generate a dashboard."*

The agent calls the tools, your browser opens `http://localhost:5173`, and it replies with the URL and "Done." It can also produce the PDF report: `update_pdf` → `download_pdf`.

**Try it without an AI client** (MCP Inspector — also requires Node):

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
- **Fully quit and reopen Claude Desktop**, start the app (`tpm-dashboard-mcp app`), then ask for a dashboard. The 🔨 icon shows `tpm-dashboard` when connected.

Cursor and any other MCP client work the same way: command = the executable, args = `["start"]`, transport = stdio.

---

## Build and run from source (development)

> `start.sh` / `stop.sh` are **source-checkout conveniences** (they locate the repo's binary or fall back to `python main.py`). If you only downloaded a release executable, ignore them — use `tpm-dashboard-mcp app` instead.

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
| `app` | the app — mock Jira + dashboard server, foreground (what Quick start runs; `start.sh` wraps it for source checkouts) |
| `start` | MCP stdio for AI clients — attaches to the app, auto-starts it if down (default) |
| `mcp` | MCP stdio only — never starts anything |
| `mock-jira` | standalone mock Jira on `:8000` |

After changing React code: `cd frontend && npm run build`, restart the app. (For hot reload during pure frontend work you can still use `npm run dev` on `:5173`, but the app is the supported way to serve data.)

## Build the single executable

```bash
cd frontend && npm install && npm run build && cd ..
pip install pyinstaller playwright && python -m playwright install chromium

# Linux / macOS
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist:frontend" --collect-all playwright main.py
# Windows (CMD) — note the semicolon
pyinstaller --onefile --name tpm-dashboard-mcp --add-data "frontend/dist;frontend" --collect-all playwright main.py
```

**`dist/tpm-dashboard-mcp` is a single executable file** — Python interpreter, all modules, every pip dependency, the built React frontend, and the Playwright driver packed inside by PyInstaller (~60–83 MB; the Chromium browser itself installs separately to `~/.cache/ms-playwright`, needed only for `update_pdf`). No Python or Node needed to run it:

```bash
./dist/tpm-dashboard-mcp app       # the app, from one file
```

Prebuilt binaries with exactly this shape are attached to every GitHub Release — building locally is only needed for development.

### Cross-platform release (CI)

GitHub Actions builds all three binaries on every `v*` tag ([`.github/workflows/release.yml`](.github/workflows/release.yml)):

```bash
git tag vX.Y.Z && git push origin main --tags
# → Linux (ubuntu-22.04 for glibc compatibility), Windows, macOS → attached to a GitHub Release
```

---

## Logging & `--debug`

Everything logs to **stderr** (stdout belongs to the MCP protocol).

The **app** prints its addresses on start (see Quick start above) plus the payload file path and Ctrl+C hint. The **MCP server** prints a banner:

```
[tpm-dashboard] MCP transport : stdio (no port/URL — your AI client spawns this process)
[tpm-dashboard] Mock Jira API : http://127.0.0.1:8000/rest/api/3/search
[tpm-dashboard] Dashboard UI  : http://localhost:5173 (from the app)
[tpm-dashboard] logging       : stderr only; normal (use --debug for verbose)
[tpm-dashboard] Dashboard     : ready → http://localhost:5173  (velocity 44.8%)
```

**`--debug` adds verbose logging:** HTTP requests/responses, payload metrics (issues/points/velocity), app auto-start with pid and readiness timing, browser-open result, and every HTTP request the app serves:

```bash
tpm-dashboard-mcp --debug app      # installed binary
./dist/tpm-dashboard-mcp --debug app
python main.py --debug app         # from source
./start.sh --debug                 # source checkout wrapper (forwards flags)
```

To debug the MCP connection, add the flag to your client config:

```json
"command": ["/path/tpm-dashboard-mcp", "--debug", "start"]
```

(The client's MCP logs then show the server's stderr — OpenCode MCP logs, Claude Desktop → `~/Library/Logs/Claude/mcp*.log` on macOS.)

## Stopping

- **Ctrl+C in the app terminal** (`tpm-dashboard-mcp app`) stops everything — both servers live in that one process. On Windows: `Ctrl+C` or `taskkill /IM tpm-dashboard-mcp.exe`. That's the full stop for binary users; no script needed.
- The MCP server handles Ctrl+C/SIGTERM too, and terminates any app *it* auto-started.
- Source checkouts can also sweep strays (old runs, stale Vite) with:

```bash
./stop.sh     # MCP server, app, mock Jira (binary or source)
```

## The four tools

| Tool | Input | Output |
|---|---|---|
| `fetch_jira_data` | none (fixed JQL: `sprint in openSprints()`) | **raw Jira v3 search response** — `{total, issues[].fields{summary,status,priority,assignee,customfield_10016,sprint}}`; the active board evolves between calls, so metrics are random each fetch; auto-starts the app if it's down |
| `generate_dashboard` | `jira_json` (raw Jira response **or** flat issue array), `open_browser` (bool, default `true`), `milestone_status` (defaults to the Jira sprint **goal**), `risks_mitigations` / `key_wins` (strings — agent passes these; Jira has no such fields) | computes metrics, writes the payload for the app, returns the URL + summary ("…velocity 44.8%, 5 issues. Done.") |
| `update_pdf` | none | headless Chromium renders the `#/pdf` layout with the latest data → `~/.cache/tpm-dashboard/sprint-health-report.pdf` (+ path/size) |
| `download_pdf` | none | JSON: `path`, `size_bytes`, `modified`, `mime_type` of the current PDF — agent flow: **`update_pdf` → `download_pdf`** |

Dashboard shows: metric cards, Milestone Status, Risks & Mitigations (severity chips), Key Wins, and a color-coded issue table (Done = green, In Progress = amber, Blocked = red). Invalid JSON produces a rendered error state instead of a crash.

## Dashboard controls (agreed behaviors)

| Control | Behavior |
|---|---|
| **Export PDF** | navigates to the `#/pdf` report page, then opens the browser print dialog (also: floating *Print / Save PDF* strip on that page) |
| **Log Risk** | modal form → appends a `Blocked` row to the table (session-local; auto-assigned key, points count toward totals) |
| **Sync (refresh)** | **live Jira sync** — the app calls the Jira API itself (`GET /api/sync`), recomputes metrics from the evolving board, keeps agent-passed risks/wins, updates the UI + toast with the new velocity (no agent needed) |
| **Sprint selector** | static label — "Sprint 24 (Current)" |
| **Ticket links / open icons** | open `https://jira.example.com/browse/<KEY>` in a new tab (placeholder host) |
| **Theme toggle** | dark ⇄ light + toast; filter chips + search filter the table client-side |

## PDF report

- **In the browser:** *Export PDF* → the print-ready report page → print dialog (or the page's *Print / Save PDF* button).
- **From your agent:** ask *"update and download the PDF"* → agent calls `update_pdf` (fresh render from latest data) then `download_pdf` (gets the file path).
- Prerequisite for `update_pdf`: Playwright Chromium once per machine — `npx playwright install chromium` (browser lives outside the executable in `~/.cache/ms-playwright`).

## Project layout

```
mock_jira.py                      Mock Jira REST API — faithful v3 subset (JQL search, issue, agile sprints), live-evolving board (port 8000)
dashboard.py                      the app runtime: dashboard server (:5173), /api/sync, payload file, app lifecycle
report.py                         shared logic: Jira fetch/normalization + payload building (MCP tools and /api/sync)
mcp_server.py                     MCPServer: four tools over stdio
main.py                           CLI entry: app | start | mcp | mock-jira
frontend/                         Vite + React + MUI app — DashboardPage, PdfPage, IssueTable, AddBlockerDialog, KpiCard (Stitch design port)
start.sh                          source-checkout convenience → the app (binary-only users: just run `tpm-dashboard-mcp app`)
stop.sh                           source-checkout convenience → stop everything
dist/tpm-dashboard-mcp            the single executable file (gitignored — built via PyInstaller/CI)
.github/workflows/release.yml     Release: PyInstaller on Linux/Windows/macOS → GitHub Release assets
REQ.md                            Requirements document (local project spec)
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser: `connection refused` on `:5173` | The tools auto-start the app when called — just ask the agent to generate once (or run `tpm-dashboard-mcp app` yourself) |
| Dashboard says "no data yet" | `generate_dashboard` hasn't run in this session → ask the agent once |
| `fetch_jira_data` returns an error | App's mock Jira down → start the app (the tool also retries after auto-start) |
| "frontend not built" | Source checkout only: `cd frontend && npm run build`, restart the app |
| Port already in use | Ctrl+C the running app (or `./stop.sh` in a source checkout), start fresh |
| MCP tools not visible in the client | Absolute path in config, restart the client, check its MCP logs |
| `update_pdf` fails with missing Chromium | `npx playwright install chromium` (browser is installed once, outside the executable) |
| Linux binary: `GLIBC_... not found` | Use the release asset (ubuntu-22.04 build) or build from source |

---

Prototype (not production) · Built with **OpenCode on MiMo-v2.6 Flash** — UI designed in **Google Stitch**, ported to React + MUI
