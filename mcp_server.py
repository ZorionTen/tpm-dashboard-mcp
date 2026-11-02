"""MCP server: fetch_jira_data + generate_dashboard tools (stdio).

The dashboard/mock live in the app process (./start.sh); this server only
hands over payload JSON via the shared file and points the agent at the URL.
"""
import json
import os
import time
import urllib.request
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
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("tpm-dashboard")
JIRA_URL = f"http://127.0.0.1:{JIRA_PORT}/rest/api/3/search"
DEBUG = os.environ.get("TPM_DEBUG") == "1"


def banner() -> None:
    _log("MCP transport : stdio (no port/URL — your AI client spawns this process)")
    _log(f"Mock Jira API : http://127.0.0.1:{JIRA_PORT}/rest/api/3/search")
    _log(f"Dashboard UI  : http://localhost:{DASH_PORT} (from ./start.sh — the app)")
    _log(f"logging       : stderr only; {'debug ON (--debug)' if DEBUG else 'normal (use --debug for verbose)'}")


def _build_payload(issues: list) -> dict:
    pts = lambda i: int(i.get("story_points") or 0)
    total = sum(pts(i) for i in issues)
    done = sum(pts(i) for i in issues if i.get("status") == "Done")
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "total_points": total,
        "done_points": done,
        "velocity": round(done / total * 100, 1) if total else 0.0,
        "issue_count": len(issues),
        "completed_count": sum(1 for i in issues if i.get("status") == "Done"),
        "issues": issues,
    }


@mcp.tool()
def fetch_jira_data() -> str:
    """Fetch current sprint issues from the mock Jira REST API. No input. Returns JSON with issues (key, summary, status, story_points). Requires the app (./start.sh) — auto-starts it if not running."""
    try:
        _dbg(f"GET {JIRA_URL}")
        with urllib.request.urlopen(JIRA_URL, timeout=5) as r:
            body = r.read().decode()
        try:
            _dbg(f"→ 200, {len(json.loads(body).get('issues', []))} issues, {len(body)} bytes")
        except Exception:
            _dbg(f"→ {len(body)} bytes")
        return body
    except Exception as e:
        _log(f"fetch_jira_data FAILED: {e}")
        ensure_app()
        try:
            with urllib.request.urlopen(JIRA_URL, timeout=5) as r:
                return r.read().decode()
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
    """Generate an HTML sprint health dashboard from Jira JSON and open it in the browser. Input: jira_json (string) — a JSON array of issues or an object with an 'issues' array (the object may also carry milestone_status, risks_mitigations, key_wins, used as defaults); open_browser (bool, optional, default true) — set false to skip opening the browser; milestone_status (string, optional, single line), risks_mitigations (string, optional, multi-line), key_wins (string, optional, multi-line) — narrative sections shown on the dashboard (empty fields are omitted). Computes total/done points and velocity %, hands the payload to the running app, and returns the dashboard URL."""
    error = None
    payload: dict
    try:
        data = json.loads(jira_json)
        issues = data.get("issues") if isinstance(data, dict) else data
        if not isinstance(issues, list):
            raise ValueError("expected a JSON array of issues or an object with an 'issues' array")
        payload = _build_payload(issues)
        # narrative fields: explicit params win, else default from the jira_json object
        if isinstance(data, dict):
            payload["milestone_status"] = milestone_status or data.get("milestone_status") or ""
            payload["risks_mitigations"] = risks_mitigations or data.get("risks_mitigations") or ""
            payload["key_wins"] = key_wins or data.get("key_wins") or ""
        else:
            payload["milestone_status"] = milestone_status
            payload["risks_mitigations"] = risks_mitigations
            payload["key_wins"] = key_wins
        _dbg(f"payload built: {payload['issue_count']} issues, {payload['total_points']} pts total, "
             f"{payload['done_points']} pts done, velocity {payload['velocity']}%, "
             f"milestone={'yes' if payload['milestone_status'] else 'no'}, "
             f"risks={'yes' if payload['risks_mitigations'] else 'no'}, "
             f"wins={'yes' if payload['key_wins'] else 'no'}")
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
        from pathlib import Path as _Path

        os.environ.setdefault(
            "PLAYWRIGHT_BROWSERS_PATH",
            str(_Path.home() / ".cache" / "ms-playwright"),
        )
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
