# AI Workflow — How This Was Built

This project was designed and coded almost entirely through AI-assisted iteration. This doc records the tools, the prompts that mattered, what the AI got wrong, and what I decided myself.

## Tools

| Tool | Role |
|---|---|
| **OpenCode** (agent harness) + **MiMo-v2.6 Flash** (model) | All code: Python backend, MCP server, React/MUI frontend, CI workflows, docs |
| **Google Stitch** (text-to-UI) | The dashboard's visual design — project *"Project Manager UI Dashboard"* (dashboard + PDF layout screens), ported to React + MUI |
| **MCP Inspector** | Manual tool testing (`npx @modelcontextprotocol/inspector …`) |
| **Playwright** | Headless PDF rendering (shipped in the binary) + scripted UI verification |
| **ElevenLabs** | AI voice-over for the walkthrough video narration |
| **GitHub Actions** | Cross-platform release builds (Linux/Windows/macOS) on every `v*` tag |

The original requirements are kept in [REQ.md](REQ.md) (superseded by the README — kept for provenance).

## Key prompts (in order of impact)

1. **Scaffold + release:** *"setup a github repo with a release — release should build and start the entire project from one executable… cross platform"* → FastAPI mock + MCP server + PyInstaller + CI in one pass.
2. **UI direction:** *"use react… replace and install MUI by Google"* → the Stitch design port, with an explicit constraint I held the agent to: *"don't assume anything, like the actions of the buttons — ask me"* → the agent came back with a question list (Export PDF, Log Risk, Sync, sprint selector, ticket links) and I picked each behavior.
3. **Realistic backend:** *"stop… make the mock server like real Jira APIs"* + *"live board, with random metrics"* → faithful Jira v3 subset (JQL, issue, agile endpoints) whose active sprint evolves on every query, plus a hard guarantee that every fetch changes a visible metric.
4. **PDF pipeline:** *"add a print/fetch pdf tool to the mcp… update tool + download tool should be used by the agent"* → `update_pdf` / `download_pdf` headless-rendering the real `#/pdf` page.
5. **Review-driven fixes:** two structured review passes (fabricated text, Team Capacity, Delivery Health, Blockers, first-open auto-load, README gaps) executed as a time-boxed cut, committing after every step.

## What the AI got wrong (and how it was fixed)

- **Ctrl+C didn't work** — the MCP SDK swallowed SIGINT; fixed with explicit signal handlers + child-process cleanup (`stop.sh` as the sweeper).
- **Release build failures** — missing `--add-data` DEST; then the Linux binary needed GLIBC 2.38 → rebuilt on `ubuntu-22.04`.
- **Frozen Playwright** looked for Chromium inside the bundle; and the MCP client's proxy env mangled `127.0.0.1` responses (`Error -3 while decompressing`) → explicit no-proxy opener for loopback.
- **PDF had a mystery white gap** — invalid MUI `print:` sx keys were silently ignored, stacking screen padding into print; fixed with proper `@media print` rules.
- **Invalid React style keys** — `bgcolor` inside `style={{}}` (works in `sx`, not in raw CSS) → `backgroundColor`.
- **Silent environment footguns** during testing: `pkill -f` patterns matching the test shell itself (zsh doesn't word-split), and a stale app process squatting on `:5173` while the new one stood down.
- **Doc rot** — a hardcoded "current: v0.4.0", dead config paths, and spec claims that no longer matched the code (two tools, plain CSS) → linked `/releases/latest`, added the "superseded" banner to `REQ.md`.

## What I decided by hand

- The button behaviors (asked, not assumed) and which review items to cut vs. keep — including dropping sprint dates/burndown from scope for the deadline.
- **Live board vs. deterministic data** — chose evolving data so every demo shows different numbers.
- **Narrative source of truth** — sprint `goal` for milestones; risks/wins *derived from the board* (blocked → risk with severity + owner, done → win) with agent params as overrides that survive sync.
- Product framing: prototype-not-production positioning, portfolio credits, removing assignment-specific text, and all scope/"future work" boundaries.
