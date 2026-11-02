"""Shared report logic: Jira fetch (never proxied), Jira-shape normalization, payload build."""
import json
import time
import urllib.request
from urllib.parse import quote

JIRA_SEARCH = (
    "http://127.0.0.1:8000/rest/api/3/search"
    f"?jql={quote('sprint in openSprints() ORDER BY status ASC')}"
    f"&fields={quote('summary,status,priority,assignee,labels,customfield_10016,sprint')}"
    "&maxResults=50"
)


def fetch_jira_raw(timeout: int = 5) -> str:
    """GET the current sprint as raw Jira v3 JSON. Never routes localhost through a proxy."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(JIRA_SEARCH, timeout=timeout) as r:
        return r.read().decode()


def normalize_jira(data) -> tuple[list, str]:
    """Accept a raw Jira search response or a flat issue list → (flat issues, sprint goal)."""
    raw = data.get("issues") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        raise ValueError("expected a Jira search response with an 'issues' array (or a flat issue array)")
    goal = ""
    if raw and isinstance(raw[0], dict) and "fields" in raw[0]:
        issues = []
        for i in raw:
            f = i.get("fields") or {}
            sp = f.get("sprint")
            sp = sp[0] if isinstance(sp, list) and sp else sp
            if not goal and isinstance(sp, dict):
                goal = sp.get("goal") or ""
            issues.append({
                "key": i.get("key", ""),
                "summary": f.get("summary", ""),
                "status": (f.get("status") or {}).get("name", ""),
                "story_points": f.get("customfield_10016") or 0,
            })
        return issues, goal
    if isinstance(data, dict):
        goal = data.get("milestone_status") or ""
    return raw, goal


def build_payload(issues: list, goal: str = "", milestone_status: str = "",
                  risks_mitigations: str = "", key_wins: str = "") -> dict:
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
        "milestone_status": milestone_status or goal,
        "risks_mitigations": risks_mitigations,
        "key_wins": key_wins,
        "issues": issues,
    }
