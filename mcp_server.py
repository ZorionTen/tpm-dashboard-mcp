"""MCP server: fetch_jira_data + generate_dashboard tools (stdio)."""
import json
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
        return  # already serving
    server = ThreadingHTTPServer(("127.0.0.1", DASH_PORT), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def _start_vite() -> None:
    if not _port_open(DASH_PORT):
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=BASE / "frontend",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(40):  # wait up to 20s for Vite
            if _port_open(DASH_PORT):
                break
            time.sleep(0.5)


@mcp.tool()
def fetch_jira_data() -> str:
    """Fetch current sprint issues from the mock Jira REST API. No input. Returns JSON with issues (key, summary, status, story_points). Requires the mock Jira server (tpm-dashboard-mcp mock-jira) to be running on port 8000."""
    try:
        with urllib.request.urlopen(JIRA_URL, timeout=5) as r:
            return r.read().decode()
    except Exception as e:
        return f"ERROR: mock Jira unreachable at {JIRA_URL}. Start it with: tpm-dashboard-mcp mock-jira ({e})"


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
    except Exception as e:
        error = f"invalid jira_json: {e}"
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
        _start_vite()
        where = str(pub / "data.json")
    time.sleep(0.3)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    if error:
        return f"ERROR: {error}. Fallback payload written; open {url} to see the error state."
    return f"Dashboard ready at {url} ({where}, velocity {payload['velocity']}%)"


if __name__ == "__main__":
    mcp.run()
