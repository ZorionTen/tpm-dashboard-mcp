"""CLI entry: tpm-dashboard-mcp [--debug] [app|start|mcp|mock-jira] (default: start).

  app     the app — mock Jira (:8000) + dashboard (:5173), foreground, Ctrl+C stops all
  start   MCP over stdio for AI clients — attaches to the app (auto-starts it if missing)
  mcp     MCP over stdio only — never starts anything
  mock-jira  standalone mock Jira on :8000

All log output goes to stderr — stdout is reserved for the MCP stdio protocol.
"""
import atexit
import os
import signal
import sys

from dashboard import JIRA_PORT, _log, ensure_app, shutdown_app


def _install_handlers() -> None:
    """Force clean exit (and app cleanup) on Ctrl+C / SIGTERM."""

    def _handler(signum, _frame):
        _log(f"signal {signal.Signals(signum).name} received — shutting down")
        shutdown_app()
        os._exit(130 if signum == signal.SIGINT else 143)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
    atexit.register(shutdown_app)


def _app_banner() -> None:
    here = sys.executable if getattr(sys, "frozen", False) else f"{sys.executable} main.py"
    _log("TPM Dashboard app")
    _log(f"Connect AI client : {here} start   (stdio MCP — Claude Desktop / OpenCode / Cursor)")
    _log(f"Ask the agent     : \"Fetch the latest Jira data and generate a dashboard\"")


def main() -> None:
    args = sys.argv[1:]
    if "--debug" in args:
        args.remove("--debug")
        os.environ["TPM_DEBUG"] = "1"
    debug = os.environ.get("TPM_DEBUG") == "1"
    cmd = args[0] if args else "start"

    if cmd == "app":
        from dashboard import run_app

        _install_handlers()
        _app_banner()
        run_app(debug)
    elif cmd == "start":
        from mcp_server import banner, mcp

        _install_handlers()
        banner()
        ensure_app()
        mcp.run()  # stdio transport
        shutdown_app()
    elif cmd == "mcp":
        from mcp_server import banner, mcp

        _install_handlers()
        banner()
        _log(f"app            : NOT auto-started (mcp subcommand) — run ./start.sh first")
        mcp.run()
        shutdown_app()
    elif cmd == "mock-jira":
        import uvicorn
        from mock_jira import app

        _log(f"Mock Jira API : starting on http://127.0.0.1:{JIRA_PORT}/rest/api/3/search"
             + ("  (debug logging ON)" if debug else ""))
        uvicorn.run(app, host="127.0.0.1", port=JIRA_PORT,
                    log_level="debug" if debug else "info")
    else:
        print(f"unknown command: {cmd}\n"
              f"usage: tpm-dashboard-mcp [--debug] [app|start|mcp|mock-jira]",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
