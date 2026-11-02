"""MCP server: fetch_jira_data + generate_dashboard tools (stdio)."""
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("tpm-dashboard")
JIRA_URL = "http://127.0.0.1:8000/rest/api/3/search"
DASH_PORT = 5173
BASE = Path(__file__).resolve().parent
FROZEN = getattr(sys, "frozen", False)
DEBUG = os.environ.get("TPM_DEBUG") == "1"


def _log(msg: str) -> None:
    """Always-visible log line (stderr — stdout is the MCP protocol)."""
    print(f"[tpm-dashboard] {msg}", file=sys.stderr, flush=True)


def _dbg(msg: str) -> None:
    """Verbose log line, only with --debug."""
    if DEBUG:
        print(f"[tpm-dashboard:debug] {msg}", file=sys.stderr, flush=True)


def banner() -> None:
    mode = "release — embedded static server" if FROZEN else "dev — writes public/data.json, spawns Vite"
    _log("MCP transport : stdio (no port/URL — your AI client spawns this process)")
    _log(f"Mock Jira API : http://127.0.0.1:8000/rest/api/3/search")
    _log(f"Dashboard UI  : http://localhost:{DASH_PORT} (served after generate_dashboard)")
    _log(f"mode          : {mode}")
    _log(f"logging       : stderr only; {'debug ON (--debug)' if DEBUG else 'normal (use --debug for verbose)'}")


def _port_open(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


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


def _static_dir() -> Path:
    if FROZEN:
        return Path(sys._MEIPASS) / "frontend"
    return BASE / "frontend" / "dist"


class _Handler(BaseHTTPRequestHandler):
    payload: dict = {}
    static: Path = _static_dir()

    def log_message(self, *args) -> None:  # silence
        pass

    def _send(self, body: bytes, ctype: str, code: int = 200) -> None:
        _dbg(f"HTTP GET {self.path} → {code} ({len(body)} bytes)")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/data.json":
            return self._send(json.dumps(self.payload).encode(), "application/json")
        f = self.static / (path.lstrip("/") or "index.html")
        if not f.is_file():
            f = self.static / "index.html"
        if not f.is_file():
            return self._send(b"frontend not built (run: npm run build)", "text/plain", 404)
        ctype = "text/html" if f.suffix == ".html" else "application/octet-stream"
        if f.suffix == ".js":
            ctype = "text/javascript"
        elif f.suffix == ".css":
            ctype = "text/css"
        self._send(f.read_bytes(), ctype)


def _serve_embedded(payload: dict) -> None:
    _Handler.payload = payload
    if _port_open(DASH_PORT):
        _dbg(f"dashboard server already serving on :{DASH_PORT} — reusing (payload updated)")
        return  # already serving
    server = ThreadingHTTPServer(("127.0.0.1", DASH_PORT), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _log(f"Dashboard UI  : embedded server started → http://localhost:{DASH_PORT}")


def _start_vite() -> None:
    if not _port_open(DASH_PORT):
        _log(f"Dashboard UI  : Vite dev server not on :{DASH_PORT} — running npm run dev ...")
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=BASE / "frontend",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for i in range(40):  # wait up to 20s for Vite
            if _port_open(DASH_PORT):
                _log(f"Dashboard UI  : Vite ready after ~{i * 0.5:.0f}s → http://localhost:{DASH_PORT}")
                return
            time.sleep(0.5)
        _log(f"WARNING: Vite not up on :{DASH_PORT} after 20s")
    else:
        _dbg(f"Vite already on :{DASH_PORT} — reusing")


@mcp.tool()
def fetch_jira_data() -> str:
    """Fetch current sprint issues from the mock Jira REST API. No input. Returns JSON with issues (key, summary, status, story_points). Requires the mock Jira server (tpm-dashboard-mcp mock-jira) to be running on port 8000."""
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
        return f"ERROR: mock Jira unreachable at {JIRA_URL}. Start it with: tpm-dashboard-mcp start ({e})"


@mcp.tool()
def generate_dashboard(jira_json: str) -> str:
    """Generate an HTML sprint health dashboard from Jira JSON and open it in the browser. Input: jira_json (string) — either a JSON array of issues or an object with an 'issues' array. Computes total/done points and velocity %, serves the React dashboard on port 5173, and opens it."""
    error = None
    payload: dict
    try:
        data = json.loads(jira_json)
        issues = data.get("issues") if isinstance(data, dict) else data
        if not isinstance(issues, list):
            raise ValueError("expected a JSON array of issues or an object with an 'issues' array")
        payload = _build_payload(issues)
        _dbg(f"payload built: {payload['issue_count']} issues, {payload['total_points']} pts total, "
             f"{payload['done_points']} pts done, velocity {payload['velocity']}%")
    except Exception as e:
        error = f"invalid jira_json: {e}"
        _log(f"generate_dashboard ERROR: {error}")
        payload = {"error": error, "issue_count": 0, "total_points": 0, "done_points": 0,
                   "velocity": 0, "completed_count": 0, "issues": []}

    url = f"http://localhost:{DASH_PORT}"
    if FROZEN:
        _serve_embedded(payload)
        where = "embedded server"
    else:  # dev: write payload for Vite, run the dev server
        pub = BASE / "frontend" / "public"
        pub.mkdir(exist_ok=True)
        (pub / "data.json").write_text(json.dumps(payload))
        _dbg(f"payload written → {pub / 'data.json'}")
        _start_vite()
        where = str(pub / "data.json")
    time.sleep(0.3)
    try:
        opened = webbrowser.open(url)
        _dbg(f"webbrowser.open({url}) → {opened}")
    except Exception as e:
        _dbg(f"webbrowser.open failed: {e} (open {url} manually)")
    if error:
        return f"ERROR: {error}. Fallback payload written; open {url} to see the error state."
    _log(f"Dashboard     : ready → {url}  (velocity {payload['velocity']}%, {where})")
    return f"Dashboard ready at {url} ({where}, velocity {payload['velocity']}%)"


if __name__ == "__main__":
    banner()
    mcp.run()
