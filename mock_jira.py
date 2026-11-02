"""Mock Jira REST API — 5 hardcoded sprint issues, port 8000."""
from fastapi import FastAPI

app = FastAPI(title="Mock Jira")

ISSUES = [
    {"key": "PROJ-101", "summary": "Design auth flow", "status": "Done", "story_points": 5},
    {"key": "PROJ-102", "summary": "Implement login API", "status": "Done", "story_points": 8},
    {"key": "PROJ-103", "summary": "Dashboard widgets", "status": "In Progress", "story_points": 8},
    {"key": "PROJ-104", "summary": "Payments integration blocked by vendor", "status": "Blocked", "story_points": 5},
    {"key": "PROJ-105", "summary": "Write onboarding docs", "status": "To Do", "story_points": 3},
]


@app.get("/rest/api/3/search")
def search() -> dict:
    return {
        "issues": ISSUES,
        "total": len(ISSUES),
        "milestone_status": "Authentication & Login API on track for the Nov 14 release",
        "risks_mitigations": (
            "- Payments integration blocked by vendor (HIGH): mitigated by feature-flagging "
            "payments for launch, weekly vendor sync\n"
            "- Dashboard widgets slipping (MED): pulling in one engineer next sprint"
        ),
        "key_wins": (
            "- Auth flow shipped ahead of schedule\n"
            "- Login API passed security review with zero findings\n"
            "- Zero Sev-1 incidents this sprint"
        ),
    }
