"""MCP server: fetch_jira_data + generate_dashboard tools (stdio).

The dashboard/mock live in the app process (./start.sh); this server only
hands over payload JSON via the shared file and points the agent at the URL.
"""
import json
import os
import time
import webbrowser

from dashboard import (
    DASH_PORT,
    JIRA_PORT,
    _dbg,
    _log,
    ensure_app,
    payload_path,
    pdf_path,
    port_open,
)
# (fetch/normalize/build live in report.py — shared with the app's /api/sync)
from report import JIRA_SEARCH, build_payload, fetch_jira_raw, normalize_jira
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("tpm-dashboard")
JIRA_URL = f"http://127.0.0.1:{JIRA_PORT}/rest/api/3/search"
DEBUG = os.environ.get("TPM_DEBUG") == "1"


def banner() -> None:
    _log("MCP transport : stdio (no port/URL — your AI client spawns this process)")
    _log(f"Mock Jira API : http://127.0.0.1:{JIRA_PORT}/rest/api/3/search")
    _log(f"Dashboard UI  : http://localhost:{DASH_PORT} (from the app)")
    _log(f"logging       : stderr only; {'debug ON (--debug)' if DEBUG else 'normal (use --debug for verbose)'}")


@mcp.tool()
def fetch_jira_data() -> str:
    """Fetch current sprint issues from the real Jira REST API shape: runs JQL 'sprint in openSprints() ORDER BY status ASC' against GET /rest/api/3/search. Returns the raw Jira response {startAt, maxResults, total, issues[].{key, fields.{summary,status,priority,assignee,customfield_10016,sprint}}} — pass the WHOLE response to generate_dashboard. The live board evolves between calls (statuses/points change). Auto-starts the app if it's down."""
    try:
        _dbg(f"GET {JIRA_SEARCH}")
        body = fetch_jira_raw()
        try:
            d = json.loads(body)
            _dbg(f"→ 200, total={d.get('total')} issues, {len(body)} bytes")
        except Exception:
            _dbg(f"→ {len(body)} bytes")
        return body
    except Exception as e:
        _log(f"fetch_jira_data FAILED: {e}")
        ensure_app()
        try:
            return fetch_jira_raw()
        except Exception as e2:
            return f"ERROR: mock Jira unreachable at {JIRA_URL} — start the app with ./start.sh ({e2})"


@mcp.tool()
def generate_dashboard(
    jira_json: str,
    open_browser: bool = True,
    milestone_status: str = "",
    risks_mitigations: str = "",
    key_wins: str = "",
) -> str:
    """Generate an HTML sprint health dashboard from Jira JSON and open it in the browser. Input: jira_json (string) — a raw Jira REST search response (issues[].fields, e.g. from fetch_jira_data), or a plain array/object with flat {key,summary,status,story_points} issues. open_browser (bool, optional, default true). milestone_status (string, optional) — defaults to the Jira sprint goal when omitted; risks_mitigations and key_wins (strings, optional, multi-line) — the agent passes these from context (the Jira API has no such fields; empty = section omitted). Computes total/done points and velocity %, hands the payload to the app, and returns the dashboard URL."""
    error = None
    payload: dict
    try:
        data = json.loads(jira_json)
        issues, goal = normalize_jira(data)
        payload = build_payload(
            issues, goal=goal, milestone_status=milestone_status,
            risks_mitigations=risks_mitigations, key_wins=key_wins,
        )
        _dbg(f"payload built: {payload['issue_count']} issues, {payload['total_points']} pts total, "
             f"{payload['done_points']} pts done, velocity {payload['velocity']}%, "
             f"milestone={'goal' if payload['milestone_status'] else 'no'}, "
             f"risks={'yes' if risks_mitigations else 'no'}, "
             f"wins={'yes' if key_wins else 'no'}")
    except Exception as e:
        error = f"invalid jira_json: {e}"
        _log(f"generate_dashboard ERROR: {error}")
        payload = {"error": error, "issue_count": 0, "total_points": 0, "done_points": 0,
                   "velocity": 0, "completed_count": 0, "issues": [],
                   "milestone_status": milestone_status, "risks_mitigations": risks_mitigations,
                   "key_wins": key_wins}

    f = payload_path()
    f.write_text(json.dumps(payload))
    _dbg(f"payload written → {f}")
    ensure_app()
    url = f"http://localhost:{DASH_PORT}"
    time.sleep(0.2)

    if not port_open(DASH_PORT):
        return f"ERROR: dashboard server not reachable on :{DASH_PORT}. Start the app (./start.sh) and retry."
    if open_browser:
        try:
            opened = webbrowser.open(url)
            _dbg(f"webbrowser.open({url}) → {opened}")
        except Exception as e:
            _dbg(f"webbrowser.open failed: {e} (open {url} manually)")
    else:
        _dbg("open_browser=false — skipping browser launch")
    if error:
        return f"ERROR: {error}. Fallback payload written; open {url} to see the error state."
    _log(f"Dashboard     : ready → {url}  (velocity {payload['velocity']}%)")
    return f"Dashboard ready at http://localhost:{DASH_PORT} — velocity {payload['velocity']}%, {payload['issue_count']} issues. Done."


@mcp.tool()
async def update_pdf() -> str:
    """Regenerate the sprint health PDF report from the latest dashboard data (headless Chromium print of the PDF layout page). Call generate_dashboard first if there is no data yet. Returns the PDF file path and size; then call download_pdf to fetch it."""
    data_file = payload_path()
    if not data_file.is_file():
        return "ERROR: no dashboard data yet — call generate_dashboard first, then update_pdf."
    ensure_app()
    if not port_open(DASH_PORT):
        return f"ERROR: dashboard server not reachable on :{DASH_PORT}. Start the app (./start.sh) and retry."
    out = pdf_path()
    _log(f"update_pdf    : rendering http://localhost:{DASH_PORT}/#/pdf → {out}")
    try:
        # In a frozen (PyInstaller) build Playwright looks for browsers inside the
        # bundle — point it at the standard user-level browser cache instead.
        # Loopback must never go through a system proxy.
        from pathlib import Path as _Path

        os.environ.setdefault(
            "PLAYWRIGHT_BROWSERS_PATH",
            str(_Path.home() / ".cache" / "ms-playwright"),
        )
        os.environ["NO_PROXY"] = "127.0.0.1,localhost,::1"
        os.environ["no_proxy"] = "127.0.0.1,localhost,::1"
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"http://localhost:{DASH_PORT}/#/pdf", wait_until="networkidle")
            await page.wait_for_selector("article", timeout=10000)
            await page.wait_for_timeout(700)  # let webfonts settle
            await page.pdf(path=str(out), format="Letter",
                           print_background=True, prefer_css_page_size=True)
            await browser.close()
    except Exception as e:
        hint = ""
        if "Executable" in str(e) or "install" in str(e).lower():
            hint = " — Chromium missing, run: npx playwright install chromium"
        _log(f"update_pdf FAILED: {e}{hint}")
        return f"ERROR: PDF generation failed: {e}{hint}"
    size = out.stat().st_size
    _log(f"update_pdf    : done — {out} ({size} bytes)")
    return f"PDF updated at {out} ({size} bytes). Call download_pdf to fetch it."


@mcp.tool()
def download_pdf() -> str:
    """Download the current sprint health PDF report. Returns the file path, size, and modified time for the agent to copy/read. If no PDF exists yet, call update_pdf first for the latest."""
    out = pdf_path()
    if not out.is_file():
        return "ERROR: no PDF yet — call update_pdf first to generate the latest report."
    st = out.stat()
    _log(f"download_pdf  : {out} ({st.st_size} bytes)")
    return json.dumps({
        "path": str(out),
        "size_bytes": st.st_size,
        "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
        "mime_type": "application/pdf",
        "note": "copy or read this file — generate_dashboard + update_pdf refresh it",
    }, indent=2)


if __name__ == "__main__":
    banner()
    mcp.run()
