"""The app: dashboard web server (:5173) + shared payload file + app lifecycle.

run_app()      — the foreground process behind ./start.sh (mock Jira + dashboard together)
ensure_app()   — used by the MCP server: attach to a running app, or spawn one detached
payload_path() — the file both processes use to hand over dashboard JSON

All log output goes to stderr — stdout is reserved for the MCP stdio protocol.
"""
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from report import build_payload, fetch_jira_raw, normalize_jira

DASH_PORT = 5173
JIRA_PORT = 8000
BASE = Path(__file__).resolve().parent
FROZEN = getattr(sys, "frozen", False)
DEBUG = os.environ.get("TPM_DEBUG") == "1"

_spawned_app = None  # Popen of an app process WE auto-started (None otherwise)


def _log(msg: str) -> None:
    print(f"[tpm-dashboard] {msg}", file=sys.stderr, flush=True)


def _dbg(msg: str) -> None:
    if DEBUG:
        print(f"[tpm-dashboard:debug] {msg}", file=sys.stderr, flush=True)


def payload_path() -> Path:
    """Shared hand-over file: MCP writes it, the app serves it at /data.json."""
    d = Path.home() / ".cache" / "tpm-dashboard"
    d.mkdir(parents=True, exist_ok=True)
    return d / "dashboard_data.json"


def pdf_path() -> Path:
    """Where update_pdf writes the sprint health report PDF."""
    d = Path.home() / ".cache" / "tpm-dashboard"
    d.mkdir(parents=True, exist_ok=True)
    return d / "sprint-health-report.pdf"


def static_dir() -> Path:
    return Path(sys._MEIPASS) / "frontend" if FROZEN else BASE / "frontend" / "dist"


def port_open(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _spawn_cmd() -> list:
    if FROZEN:
        return [sys.executable, "app"]
    return [sys.executable, str((BASE / "main.py").resolve()), "app"]


def ensure_app() -> None:
    """Start the app detached if either port is down; wait until ready."""
    global _spawned_app
    down = [p for p in (JIRA_PORT, DASH_PORT) if not port_open(p)]
    if not down:
        _dbg("app already running (both ports up) — attaching")
        return
    if _spawned_app is None:
        _log(f"app not running (down: {down}) — auto-starting: {' '.join(_spawn_cmd())}")
        _spawned_app = subprocess.Popen(
            _spawn_cmd(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _log(f"              → pid {_spawned_app.pid}")
    for _ in range(48):  # wait up to 12s
        if all(port_open(p) for p in down):
            _log("              → app ready: "
                 f"http://127.0.0.1:{JIRA_PORT}/rest/api/3/search, http://localhost:{DASH_PORT}")
            return
        time.sleep(0.25)
    _log(f"WARNING: app did not come up within 12s (still down: {down})")


def shutdown_app() -> None:
    """Terminate the app only if THIS process spawned it (idempotent)."""
    global _spawned_app
    if _spawned_app is not None and _spawned_app.poll() is None:
        _log(f"stopping auto-started app (pid {_spawned_app.pid})")
        _spawned_app.terminate()
        try:
            _spawned_app.wait(timeout=3)
        except Exception:
            _spawned_app.kill()
    _spawned_app = None


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *_a) -> None:
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
        if path == "/api/sync":
            return self._sync()
        if path == "/data.json":
            f = payload_path()
            if not f.is_file():
                return self._send(
                    json.dumps({"error": "no data yet - ask your agent to generate a dashboard"}).encode(),
                    "application/json")
            return self._send(f.read_bytes(), "application/json")
        f = static_dir() / (path.lstrip("/") or "index.html")
        if not f.is_file():
            f = static_dir() / "index.html"
        if not f.is_file():
            return self._send(b"frontend not built (run: cd frontend && npm run build)",
                              "text/plain", 404)
        ctype = {"html": "text/html", "js": "text/javascript", "css": "text/css"}.get(
            f.suffix.lstrip("."), "application/octet-stream")
        self._send(f.read_bytes(), ctype)

    def _sync(self) -> None:
        """Live sync: pull the board from the mock Jira, keep agent-passed narrative,
        refresh the payload — this is what the dashboard's Sync button calls."""
        try:
            data = json.loads(fetch_jira_raw())
            issues, goal = normalize_jira(data)
            f = payload_path()
            old = json.loads(f.read_text()) if f.is_file() else {}
            # keep agent-passed narrative; re-derive anything the server generated
            old_risks = "" if old.get("risks_source") == "derived" else old.get("risks_mitigations", "")
            old_wins = "" if old.get("wins_source") == "derived" else old.get("key_wins", "")
            payload = build_payload(
                issues,
                goal=goal or old.get("milestone_status", ""),
                risks_mitigations=old_risks,
                key_wins=old_wins,
            )
            f.write_text(json.dumps(payload))
            _dbg(f"api/sync → {payload['issue_count']} issues, velocity {payload['velocity']}% (live)")
            return self._send(json.dumps(payload).encode(), "application/json")
        except Exception as e:
            _log(f"api/sync FAILED: {e}")
            return self._send(
                json.dumps({"error": f"live sync failed: {e}"}).encode(),
                "application/json", 502)


def run_app(debug: bool = False) -> None:
    """Foreground app: mock Jira on :8000 + dashboard on :5173 (skips busy ports)."""
    if port_open(JIRA_PORT):
        _log(f"Mock Jira API : already running → http://127.0.0.1:{JIRA_PORT}/rest/api/3/search")
    else:
        import uvicorn
        from mock_jira import app

        config = uvicorn.Config(app, host="127.0.0.1", port=JIRA_PORT,
                                log_level="debug" if debug else "info")
        threading.Thread(target=uvicorn.Server(config).run, daemon=True).start()
        _log(f"Mock Jira API : starting → http://127.0.0.1:{JIRA_PORT}/rest/api/3/search")

    if port_open(DASH_PORT):
        _log(f"Dashboard UI  : already running → http://localhost:{DASH_PORT}")
    else:
        threading.Thread(
            target=ThreadingHTTPServer(("127.0.0.1", DASH_PORT), _Handler).serve_forever,
            daemon=True,
        ).start()
        _log(f"Dashboard UI  : starting → http://localhost:{DASH_PORT}")

    for _ in range(40):
        if port_open(JIRA_PORT) and port_open(DASH_PORT):
            break
        time.sleep(0.25)
    _log(f"ready          mock Jira http://127.0.0.1:{JIRA_PORT}/rest/api/3/search"
         f" | dashboard http://localhost:{DASH_PORT}")
    _log(f"payload file   {payload_path()}")
    _log("Ctrl+C stops the app (or run ./stop.sh from another terminal)")

    threading.Event().wait()  # signals are handled in main.py → os._exit
