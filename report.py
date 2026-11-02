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
                "assignee": (f.get("assignee") or {}).get("displayName", ""),
            })
        return issues, goal
    if isinstance(data, dict):
        goal = data.get("milestone_status") or ""
    return raw, goal


def _severity(points: int) -> str:
    return "HIGH" if points >= 8 else "MED" if points >= 5 else "LOW"


def derive_risks(issues: list) -> str:
    """Risks straight from the board: every Blocked issue, plus large unstarted scope."""
    lines = []
    for i in issues:
        pts, owner = int(i.get("story_points") or 0), i.get("assignee") or "unassigned"
        if i.get("status") == "Blocked":
            lines.append(f"- {i['summary']} ({_severity(pts)}): {pts} pts blocked, owner {owner}")
        elif i.get("status") == "To Do" and pts >= 8:
            lines.append(f"- {i['summary']} (MED): {pts} pts not started yet, owner {owner}")
    return "\n".join(lines)


def derive_wins(issues: list) -> str:
    """Key wins straight from the board: every completed issue."""
    return "\n".join(
        f"- {i['summary']} ({int(i.get('story_points') or 0)} pts delivered)"
        for i in issues if i.get("status") == "Done"
    )


CAPACITY_PTS = 8  # assumed per-person sprint capacity (documented in the README)


def _capacity(issues: list) -> list:
    """Per-person committed/done points vs an assumed 8-pt sprint capacity."""
    by = {}
    for i in issues:
        name = (i.get("assignee") or "").strip() or "Unassigned"
        e = by.setdefault(name, {"name": name, "committed_pts": 0, "done_pts": 0, "issues": 0})
        p = int(i.get("story_points") or 0)
        e["committed_pts"] += p
        e["issues"] += 1
        if i.get("status") == "Done":
            e["done_pts"] += p
    out = []
    for e in by.values():
        e["capacity_pts"] = CAPACITY_PTS
        e["load_pct"] = round(e["committed_pts"] / CAPACITY_PTS * 100)
        out.append(e)
    return sorted(out, key=lambda x: -x["load_pct"])


def _health(issues: list, total: int, done_pts: int) -> dict:
    """Simplified delivery health (explainable rule, no dates needed):
    Off Track = blocked points > 25% of scope or velocity < 25%;
    At Risk = any blocker; else On Track."""
    blocked = [i for i in issues if i.get("status") == "Blocked"]
    bpts = sum(int(i.get("story_points") or 0) for i in blocked)
    velocity = round(done_pts / total * 100, 1) if total else 0.0
    blocked_pct = round(bpts / total * 100, 1) if total else 0.0
    if blocked_pct > 25 or velocity < 25:
        status = "Off Track"
    elif blocked:
        status = "At Risk"
    else:
        status = "On Track"
    reasons = []
    if blocked:
        reasons.append(f"{len(blocked)} blocked ticket{'s' if len(blocked) > 1 else ''} ({bpts} pts, {blocked_pct}% of scope)")
    if velocity < 25:
        reasons.append(f"velocity {velocity}% is below the 25% floor")
    elif status != "On Track":
        reasons.append(f"velocity {velocity}%")
    if status == "On Track":
        reasons = [f"velocity {velocity}%", "no blockers"]
    return {"status": status, "reasons": reasons}


def build_payload(issues: list, goal: str = "", milestone_status: str = "",
                  risks_mitigations: str = "", key_wins: str = "") -> dict:
    """Build the dashboard payload. Empty risks/wins are DERIVED from the board itself
    (Blocked → risks, Done → wins); explicit params always win."""
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
        "risks_mitigations": risks_mitigations or derive_risks(issues),
        "key_wins": key_wins or derive_wins(issues),
        "risks_source": "agent" if risks_mitigations else "derived",
        "wins_source": "agent" if key_wins else "derived",
        "team_capacity": _capacity(issues),
        "health": _health(issues, total, done),
        "issues": issues,
    }
