# Part 11 — AI Productivity Utility: Requirements Document

**Product:** TPM Dashboard MCP Server
**Chosen Option:** Option E (Project Health Dashboard) — delivered as an MCP tool, frontend in React, shipped as a single cross-platform executable
**Author:** Zaid
**Date:** November 2026
**Status:** Prototype (MVP)
**Audience:** Developer / AI-assisted build (Cursor, Claude Code)

---

## 1. Problem Statement

Technical Program Managers waste time manually pulling sprint data from Jira into slide decks or spreadsheets to show leadership a simple health snapshot. The data already exists; the friction is in the retrieval and the formatting.

**Result:** Status updates are delayed, inconsistent, and often out of date by the time they reach leadership.

---

## 2. User Persona

**Primary User:** A Technical Program Manager who needs a quick, visual sprint health snapshot every Friday.

**Pain Points:**
- Clicking through Jira filters manually
- Copy-pasting issue lists into slides
- No single view that shows velocity + blockers + status at a glance
- The dashboard is stale by Monday

**Goal:** Ask an AI agent for the current sprint health and get a browser dashboard in under 10 seconds.

---

## 3. User Story

**ID:** US-P11-01
**Title:** Generate a live sprint dashboard from Jira via an AI agent

**As a** Technical Program Manager,
**I want to** ask my AI client (OpenCode, Claude Desktop, Cursor) to fetch the latest Jira data and open a health dashboard in my browser,
**So that** I can see sprint velocity, issue status, and blockers without opening Jira or building a slide deck.

---

## 4. Acceptance Criteria

| # | Criterion | Test |
|---|---|---|
| AC1 | The MCP server exposes two tools: `fetch_jira_data` and `generate_dashboard` | MCP Inspector lists both tools |
| AC2 | `fetch_jira_data` returns structured JSON from a mock Jira REST API | Call tool via Inspector; JSON appears |
| AC3 | `generate_dashboard` accepts the JSON, computes velocity (done points / total points), and persists it for the React frontend | Call tool with sample JSON; payload is served at `/data.json` |
| AC4 | The generated dashboard opens automatically in the user's default browser at `http://localhost:5173` | Browser launches after tool call |
| AC5 | The dashboard shows: total issues, completed issues, velocity ratio, and a list of issues with status | Visual inspection of rendered React UI |
| AC6 | The MCP server runs over stdio and connects to OpenCode (or any MCP client) | OpenCode calls the tool via natural language |
| AC7 | The mock Jira server runs locally on port 8000 with no external dependencies | `tpm-dashboard-mcp mock-jira` starts without errors |
| AC8 | The frontend is a Vite + React app rendered with components (not static HTML) | `frontend/src` contains React components rendering metrics and issue table |
| AC9 | A release provides one executable per OS that runs the entire project with no Python/Node install | GitHub Release assets: Linux, Windows, macOS binaries; each runs `app` and `start` |
| AC10 | The dashboard shows Milestone Status (single line), Risks & Mitigations (multi-line), and Key Wins (multi-line); empty fields are omitted | Visual inspection of rendered React UI; call generate with/without the fields |
| AC11 | The MCP exposes `update_pdf` and `download_pdf`: update renders the PDF layout page headlessly to a PDF file; download returns its path/metadata | Call both via Inspector after generate_dashboard; a valid PDF file appears in `~/.cache/tpm-dashboard/` |
| AC12 | The UI is the Stitch design ("Project Manager UI Dashboard") implemented in React + MUI: dashboard page and PDF layout page, with the agreed button behaviors (Export PDF → PDF page + print dialog; Log Risk → session-local modal; Sync → re-fetch `/data.json`; static sprint label; fake Jira links) | Visual comparison against the Stitch screens; click each control |

---

## 5. Functional Requirements

### 5.1 System Overview

The solution has four components:

1. **The app** — one foreground process (started by `./start.sh`) hosting two servers: a mock Jira API (fake sprint data, no real Jira credentials) and the dashboard web server. Prints its addresses on start; Ctrl+C stops both.
2. **An MCP server** — exposes two tools to any MCP-compatible AI client: one to fetch Jira data, one to hand the payload to the app and return the dashboard URL. Spawned by the AI client over stdio on connect ("MCP connects"); attaches to a running app, auto-starts one if the user skipped step 1.
3. **A React frontend** — a Vite + React app that reads the generated JSON and renders the health dashboard. Its production build is bundled into the executable and served by the app.
4. **The user's AI client** — OpenCode (or Claude Desktop, Cursor) — acts as the control plane. The user asks in natural language; the client calls the tools.

**Packaging:** one entry point (`main.py`) is compiled with PyInstaller into a single cross-platform executable per OS (`tpm-dashboard-mcp`), with subcommands:

```
tpm-dashboard-mcp app           → THE APP: mock Jira :8000 + dashboard :5173, foreground (what ./start.sh runs)
tpm-dashboard-mcp start         → stdio MCP server (default; what AI clients run) — attaches to the app, auto-starts it if down
tpm-dashboard-mcp mock-jira     → FastAPI mock Jira on :8000 (standalone)
tpm-dashboard-mcp mcp           → stdio MCP server only (starts nothing)
```

**Architecture flow (the target user flow):**

```
1. User starts the app        ./start.sh        → mock Jira :8000 + dashboard :5173 (stays running)
2. User starts Claude/OpenCode (config: <executable> start)
                             → client spawns MCP server (stdio) → connects, attaches to the app
3. User asks for an update    → agent calls fetch_jira_data → JSON
                             → agent calls generate_dashboard → payload written for the app
                             → browser opens http://localhost:5173, agent replies with the URL + "Done."
```

```
User ── ./start.sh ──▶ APP PROCESS ── mock Jira :8000 ──▶ React dashboard :5173
                          ▲                                    ▲
AI client ── spawns ── MCP server (stdio) ── fetch / generate ─┘
                                          (shared payload file ~/.cache/tpm-dashboard/dashboard_data.json)
```

### 5.2 Component Requirements

**Component 1: Mock Jira API**

| Requirement | Detail |
|---|---|
| Purpose | Simulate a Jira REST endpoint for local testing |
| Tech | Python + FastAPI + Uvicorn |
| Endpoint | `GET /rest/api/3/search` |
| Response | JSON with 5 issues (key, summary, status, story_points) plus sprint narrative fields: `milestone_status` (single line), `risks_mitigations` (multi-line), `key_wins` (multi-line) — sample data for the dashboard |
| Port | 8000 |
| Auth | None (prototype only) |

**Component 2: MCP Server**

| Requirement | Detail |
|---|---|
| Purpose | Expose tools to an AI client via the Model Context Protocol |
| Tech | Python + `mcp` SDK (`MCPServer`, v2) |
| Transport | stdio (standard for local MCP servers) |
| Tools | `fetch_jira_data`, `generate_dashboard`, `update_pdf`, `download_pdf` |
| Dependency | The app provides the data (`:8000`) and the dashboard (`:5173`); the MCP server attaches and may auto-start it. `update_pdf` needs Playwright Chromium (`npx playwright install chromium`) |

**Tool 1: `fetch_jira_data`**

| Field | Detail |
|---|---|
| Description | "Fetch current sprint issues from the mock Jira REST API." |
| Input | None |
| Output | JSON string of issues |
| Logic | HTTP GET to `http://localhost:8000/rest/api/3/search`; return response as JSON |
| Error handling | If unreachable: auto-start the app once and retry; otherwise return an actionable error message |

**Tool 2: `generate_dashboard`**

| Field | Detail |
|---|---|
| Description | "Generate an HTML sprint health dashboard from Jira JSON and open it in the browser." |
| Input | `jira_json` (string), `open_browser` (bool, optional, default `true`), `milestone_status` (string, optional, single line), `risks_mitigations` (string, optional, multi-line), `key_wins` (string, optional, multi-line) |
| Output | Dashboard URL + one-line summary ("…velocity 44.8%, 5 issues. Done.") — what the agent reports back |
| Logic | 1. Parse JSON (array of issues, or object with `issues` array). 2. Compute total points, done points, velocity ratio. 3. If the narrative params are empty and `jira_json` is an object, default them from `milestone_status` / `risks_mitigations` / `key_wins` keys in the payload (explicit params win). 4. Write the payload to the shared file (`~/.cache/tpm-dashboard/dashboard_data.json`) that the app serves at `/data.json`. 5. Ensure the app is up (attach / auto-start). 6. If `open_browser`, open `http://localhost:5173` via `webbrowser.open()`. |
| Error handling | Return an error if JSON is invalid; still write a fallback payload so the React app renders an error state. If `:5173` is unreachable, return an actionable error (start the app) |

**Tool 3: `update_pdf`**

| Field | Detail |
|---|---|
| Description | "Regenerate the sprint health PDF report from the latest dashboard data." |
| Input | None (data comes from the shared payload; call `generate_dashboard` first if empty) |
| Output | Success message with PDF path + size, or an actionable error (incl. missing-Chromium hint) |
| Logic | Ensure the app is up → headless Playwright Chromium opens `http://localhost:5173/#/pdf` → `page.pdf(format=Letter, print_background, prefer_css_page_size)` → writes `~/.cache/tpm-dashboard/sprint-health-report.pdf` |

**Tool 4: `download_pdf`**

| Field | Detail |
|---|---|
| Description | "Download the current sprint health PDF report." |
| Input | None |
| Output | JSON: `path`, `size_bytes`, `modified`, `mime_type` (agent copies/reads the file) |
| Error handling | If no PDF exists: "call update_pdf first" |

**Component 3: React Frontend**

| Requirement | Detail |
|---|---|
| Purpose | Render the sprint health dashboard from generated JSON |
| Tech | Vite + React with **MUI (Material UI)**; design ported from Google Stitch ("Project Manager UI Dashboard"); Inter/Roboto Mono/Material Symbols fonts |
| Port | 5173, served by the app process (built `frontend/dist`, bundled in the executable) |
| Data source | `/data.json` fetched at render time (written by the MCP tool, served from `~/.cache/tpm-dashboard/dashboard_data.json`) |
| Components | `App` → `MetricCard`, `IssueTable` (one concern per component) |
| Styling | Plain CSS (dark background, card-based metrics, clean sans-serif); no UI framework |
| External deps | None at runtime — no CDN, no API calls from the browser |
| Packaging | `npm run build` output (`frontend/dist`) is bundled into the executable as data files |

### 5.3 Dashboard Output Requirements

The React app must display:

| Element | Requirement |
|---|---|
| Header | "Sprint Health Dashboard" |
| Metrics cards | Total Points, Done Points, Velocity %, Issue Count, Completed Issues |
| Milestone Status | Single line of text, shown as its own section (omitted when empty) |
| Risks & Mitigations | Multi-line text, rendered as one bullet per line (omitted when empty) |
| Key Wins | Multi-line text, rendered as one bullet per line (omitted when empty) |
| Issue table | Columns: Key, Summary, Status, Story Points |
| Status color coding | Done = green; In Progress = amber; Blocked = red |
| Footer | "Generated by TPM Dashboard MCP · Prototype" |

Visual style: dark background, clean sans-serif, card-based metrics. Rendering happens in React components; data arrives via `/data.json`.

---

## 6. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Setup time | Under 5 minutes from clone to running |
| Runtime | Dashboard generation under 10 seconds (release mode: no build/dev-server step) |
| Dependencies | Runtime: the executable (+ Playwright Chromium for `update_pdf`: `npx playwright install chromium`). Dev: Python 3.10+, Node 18+, 4 pip packages (`mcp`, `fastapi`, `uvicorn`, `playwright`). Testing: one npm package (`@modelcontextprotocol/inspector`) |
| Distribution | GitHub Releases: one single-file executable per OS (Linux x86_64, Windows x86_64, macOS arm64), built by CI on every `v*` tag |
| Portability | Runs on macOS, Linux, Windows (anywhere Python runs) |
| No external services | No real Jira, no cloud, no API keys |
| Code size | Python under 500 lines across all files; React frontend small and componentized |
| Logging | Startup banner (transport, addresses, mode) on stderr always; `--debug` for verbose tool/HTTP logging; stdout reserved for the MCP protocol |
| Shutdown | Ctrl+C / SIGTERM terminate auto-started children (mock Jira, Vite) and exit; `stop.sh` stops everything including orphans |

---

## 7. Deliverables

| # | Deliverable | Detail |
|---|---|---|
| 1 | GitHub repository | Public repo: `tpm-dashboard-mcp` |
| 2 | `mock_jira.py` | FastAPI mock Jira server |
| 3 | `mcp_server.py` | MCP server with two tools |
| 4 | `dashboard.py` | The app runtime: dashboard server (`:5173`), shared payload file, app lifecycle (ensure/attach/spawn/stop) |
| 5 | `main.py` | Single CLI entry (`app` \| `start` \| `mcp` \| `mock-jira`) used by both dev and packaging |
| 6 | `frontend/` | Vite + React app (`src/App.jsx`, components, CSS) |
| 7 | `requirements.txt` | Python dependencies |
| 8 | `README.md` | Setup, architecture, how to connect to OpenCode/Claude Desktop, video link |
| 9 | `.gitignore` | Exclude `frontend/public/data.json`, `node_modules/`, `__pycache__/`, `dist/`, `frontend/dist/` |
| 10 | `start.sh` / `stop.sh` | One-command start (the app: launcher with binary → source fallback) and stop (kills MCP, app, mock Jira) |
| 11 | Release workflow | `.github/workflows/release.yml` — PyInstaller single-file build on Linux/Windows/macOS, attached to a GitHub Release on every `v*` tag |
| 12 | GitHub Release | Cross-platform executables downloadable from the Releases page |
| 13 | Loom video (10–15 min) | Problem → demo → code walkthrough → connection to Parts 1–10 |

---

## 8. Out of Scope (Prototype Boundaries)

- Real Jira authentication (OAuth, API tokens)
- Persistent data storage
- Multi-user support
- Deployed hosting (frontend served locally; release is a desktop-style local binary)
- Scheduled/automatic report generation
- Slack/email delivery of the dashboard
- Real-time Jira sync
- Code signing / notarization of release binaries

These are listed as "future work" in the README to show product thinking without building them.

---

## 9. Definition of Done

- [ ] `./start.sh` starts the app (mock Jira on 8000 + dashboard on 5173) with printed addresses; Ctrl+C stops both
- [ ] `mcp_server.py` exposes both tools and is verified via MCP Inspector / OpenCode
- [ ] `generate_dashboard` serves the React dashboard at `http://localhost:5173` and opens the browser
- [ ] React app renders metrics cards and the color-coded issue table from `/data.json`
- [ ] Single-file executable builds locally with PyInstaller and runs the `app` and `start` subcommands
- [ ] `generate_dashboard` → `update_pdf` → `download_pdf` produces a valid PDF at `~/.cache/tpm-dashboard/sprint-health-report.pdf`
- [ ] GitHub Release created by CI with Linux, Windows, and macOS executables
- [ ] GitHub repo is public with a complete README
- [ ] Loom video (10–15 min) recorded and linked

---

## 10. Build Plan (Developer Handoff Notes)

These are notes for the developer (or AI coding assistant). They describe *what* to build, not *how* to write the code.

### Step 1: Scaffold the mock Jira
- A single Python file with a FastAPI app
- One endpoint that returns 5 hardcoded issues
- Runs on port 8000
- Verify with `curl http://localhost:8000/rest/api/3/search`

### Step 2: Scaffold the React frontend
- `npm create vite@latest frontend -- --template react`
- Build components: `MetricCard`, `IssueTable`, composed in `App`
- Fetch `/data.json` on mount; render an error state if missing
- Dark, card-based styling in plain CSS
- Fixed port 5173 (strict) so the MCP tool URL is stable

### Step 3: Scaffold the MCP server
- A single Python file using the `mcp` SDK's `MCPServer`
- Two `@mcp.tool()` decorated functions: `fetch_jira_data` and `generate_dashboard`
- `generate_dashboard` computes metrics, persists the payload, starts/serves the frontend, and opens the browser
- Tools must have clear docstrings (the AI client reads these to understand when to call them)
- A shared `main.py` entry dispatches `mock-jira` vs `mcp` subcommands

### Step 4: Test with MCP Inspector
- Run the mock Jira in one terminal
- Run `npx @modelcontextprotocol/inspector python main.py mcp` in another
- Call both tools manually and verify output

### Step 5: Connect to OpenCode
- Add the MCP server to OpenCode's config
- Restart OpenCode
- Test with: *"Fetch the latest Jira data and generate a dashboard."*

### Step 6: Package the single executable
- `npm run build` the frontend
- PyInstaller `--onefile` with `frontend/dist` bundled as data
- Verify both subcommands from the binary

### Step 7: Release via CI
- GitHub Actions workflow: build frontend → PyInstaller on Linux/Windows/macOS → attach binaries to a GitHub Release on every `v*` tag
- Tag `v0.1.0`, confirm all three assets appear on the Releases page

### Step 8: Push, document, record
- Push to GitHub
- Write README covering: problem, architecture, setup steps, how to connect to OpenCode, release download, video link
- Record the video: 2 min problem → 3 min live demo in OpenCode → 2 min the two tools + React components → 3 min connection to Parts 1–10 → 2 min challenges and future work

---

## 11. Why This Qualifies for Full Marks

| Brief Requirement | How This Delivers |
|---|---|
| "Improves productivity of a TPM" | Eliminates manual Jira → slide deck workflow |
| "Leverage AI tools" | Built in Cursor/Claude Code; used as an MCP tool inside OpenCode |
| "Problem-solving approach" | Identifies the retrieval-to-presentation gap |
| "Product thinking" | Clear persona, user story, acceptance criteria, out-of-scope boundaries |
| "Rapid prototyping" | Two Python files + a small React app, no deployment, mock data |
| "GitHub Repository + README" | Explicit deliverable, plus CI-built releases |
| "Working application" | Live demo via MCP Inspector + OpenCode + React dashboard, distributed as one executable |
| "AI prompts or workflow" | Tool descriptions and build plan included in README |

---

## 12. One-Line Pitch (For the Video)

> *"I didn't build a dashboard. I built an MCP server that lets any AI agent fetch Jira data and render a React health dashboard on demand — packaged as a single executable for any OS. The AI client is the UI. The tools are the product."*

---

*End of Requirements Document — Part 11*
