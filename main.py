"""CLI entry point: `tpm-dashboard-mcp [mock-jira|mcp]` (default: mcp)."""
import sys


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "mcp"
    if cmd == "mock-jira":
        import uvicorn
        from mock_jira import app

        uvicorn.run(app, host="127.0.0.1", port=8000)
    elif cmd == "mcp":
        from mcp_server import mcp

        mcp.run()  # stdio transport
    else:
        print(f"unknown command: {cmd}\nusage: tpm-dashboard-mcp [mock-jira|mcp]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
