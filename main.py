"""CLI entry: tpm-dashboard-mcp [start|mock-jira|mcp] (default: start)."""
import sys


def _spawn_mock_jira() -> None:
    """Start mock-jira detached unless port 8000 is already serving."""
    import socket
    import subprocess
    from pathlib import Path

    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", 8000)) == 0:
            return
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "mock-jira"]
    else:
        cmd = [sys.executable, str(Path(__file__).resolve()), "mock-jira"]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    import time

    for _ in range(40):  # wait up to 10s for uvicorn to come up
        time.sleep(0.25)
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8000)) == 0:
                return


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "mock-jira":
        import uvicorn
        from mock_jira import app

        uvicorn.run(app, host="127.0.0.1", port=8000)
    elif cmd in ("mcp", "start"):
        if cmd == "start":
            _spawn_mock_jira()
        from mcp_server import mcp

        mcp.run()  # stdio transport
    else:
        print(f"unknown command: {cmd}\nusage: tpm-dashboard-mcp [start|mock-jira|mcp]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
