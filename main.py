"""CLI entry: tpm-dashboard-mcp [--debug] [start|mock-jira|mcp] (default: start).

All log output goes to stderr — stdout is reserved for the MCP stdio protocol.
Ctrl+C / SIGTERM shut down cleanly, including any auto-started child processes.
"""
import atexit
import os
import signal
import sys

_spawned_mock = None  # Popen of the mock Jira we auto-started (None if we didn't spawn it)


def _log(msg: str) -> None:
    print(f"[tpm-dashboard] {msg}", file=sys.stderr, flush=True)


def _shutdown() -> None:
    """Terminate everything this process auto-started (idempotent)."""
    global _spawned_mock
    if _spawned_mock is not None and _spawned_mock.poll() is None:
        _log(f"stopping auto-started Mock Jira (pid {_spawned_mock.pid})")
        _spawned_mock.terminate()
        try:
            _spawned_mock.wait(timeout=3)
        except Exception:
            _spawned_mock.kill()
    _spawned_mock = None
    try:
        from mcp_server import shutdown as mcp_shutdown

        mcp_shutdown()
    except Exception:
        pass


def _install_handlers() -> None:
    """The MCP SDK can swallow SIGINT — install our own force-exit handlers."""

    def _handler(signum, _frame):
        _log(f"signal {signal.Signals(signum).name} received — shutting down")
        _shutdown()
        os._exit(130 if signum == signal.SIGINT else 143)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
    atexit.register(_shutdown)


def _spawn_mock_jira() -> None:
    """Start mock-jira detached unless port 8000 is already serving."""
    import socket
    import subprocess
    import time
    from pathlib import Path

    global _spawned_mock
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", 8000)) == 0:
            _log("Mock Jira API : http://127.0.0.1:8000/rest/api/3/search (already running)")
            return
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "mock-jira"]
    else:
        cmd = [sys.executable, str(Path(__file__).resolve()), "mock-jira"]
    _log(f"Mock Jira API : auto-starting detached: {' '.join(cmd)}")
    _spawned_mock = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
    )
    _log(f"              → pid {_spawned_mock.pid}, waiting for http://127.0.0.1:8000 ...")
    for _ in range(40):  # wait up to 10s for uvicorn to come up
        time.sleep(0.25)
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8000)) == 0:
                _log("              → ready: http://127.0.0.1:8000/rest/api/3/search")
                return
    _log("WARNING: mock Jira did not come up within 10s — fetch_jira_data will fail")


def main() -> None:
    args = sys.argv[1:]
    if "--debug" in args:
        args.remove("--debug")
        os.environ["TPM_DEBUG"] = "1"
    cmd = args[0] if args else "start"

    if cmd == "mock-jira":
        debug = os.environ.get("TPM_DEBUG") == "1"
        _log("Mock Jira API : starting on http://127.0.0.1:8000/rest/api/3/search"
             + ("  (debug logging ON)" if debug else ""))
        import uvicorn
        from mock_jira import app

        uvicorn.run(app, host="127.0.0.1", port=8000,
                    log_level="debug" if debug else "info")
    elif cmd in ("mcp", "start"):
        from mcp_server import banner, mcp

        banner()
        if cmd == "start":
            _spawn_mock_jira()
        else:
            _log("Mock Jira API : NOT auto-started (mcp subcommand) — run 'mock-jira' separately")
        _install_handlers()
        mcp.run()  # stdio transport
        _shutdown()
    else:
        print(f"unknown command: {cmd}\nusage: tpm-dashboard-mcp [--debug] [start|mock-jira|mcp]",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
