"""Mock Jira REST API — 4 sprint datasets, one random dataset per request. Port 8000."""
import random

from fastapi import FastAPI

app = FastAPI(title="Mock Jira")

DATASETS = [
    {  # 1: Authentication & Login API (the original)
        "issues": [
            {"key": "PROJ-101", "summary": "Design auth flow", "status": "Done", "story_points": 5},
            {"key": "PROJ-102", "summary": "Implement login API", "status": "Done", "story_points": 8},
            {"key": "PROJ-103", "summary": "Dashboard widgets", "status": "In Progress", "story_points": 8},
            {"key": "PROJ-104", "summary": "Payments integration blocked by vendor", "status": "Blocked", "story_points": 5},
            {"key": "PROJ-105", "summary": "Write onboarding docs", "status": "To Do", "story_points": 3},
        ],
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
    },
    {  # 2: Payments rollout hardening
        "issues": [
            {"key": "PROJ-201", "summary": "Rate limiter rollout", "status": "Done", "story_points": 3},
            {"key": "PROJ-202", "summary": "Vendor sandbox re-certification", "status": "In Progress", "story_points": 5},
            {"key": "PROJ-203", "summary": "Checkout retry logic", "status": "In Progress", "story_points": 8},
            {"key": "PROJ-204", "summary": "Fraud rules engine integration", "status": "Blocked", "story_points": 13},
            {"key": "PROJ-205", "summary": "Rollout docs refresh", "status": "To Do", "story_points": 2},
        ],
        "milestone_status": "Payments certification 60% complete, gate review Nov 21",
        "risks_mitigations": (
            "- Fraud rules engine blocked on training data (HIGH): data team provisioning "
            "synthetic corpus, daily standup until cleared\n"
            "- Checkout retry logic scope growth (MED): frozen at 8 pts, PM review on any change"
        ),
        "key_wins": (
            "- Rate limiter shipped 2 days early\n"
            "- Zero checkout regressions in load test\n"
            "- Vendor sandbox certified for staging"
        ),
    },
    {  # 3: Mobile app beta
        "issues": [
            {"key": "PROJ-301", "summary": "Push notification service", "status": "Done", "story_points": 5},
            {"key": "PROJ-302", "summary": "Offline cache layer", "status": "In Progress", "story_points": 8},
            {"key": "PROJ-303", "summary": "Beta feedback triage", "status": "In Progress", "story_points": 3},
            {"key": "PROJ-304", "summary": "iOS build pipeline", "status": "Blocked", "story_points": 5},
            {"key": "PROJ-305", "summary": "Analytics events audit", "status": "To Do", "story_points": 3},
        ],
        "milestone_status": "Closed beta with 200 users starts Nov 18",
        "risks_mitigations": (
            "- iOS signing certificate expiry (HIGH): renewed cert, rotating through CI this week\n"
            "- Offline cache memory growth (MED): profiling sprint, cap at 50MB per session"
        ),
        "key_wins": (
            "- Crash-free rate held at 99.7%\n"
            "- Beta build approved by app store review\n"
            "- Push open-rate up 18% vs email"
        ),
    },
    {  # 4: Data platform migration
        "issues": [
            {"key": "PROJ-401", "summary": "Warehouse schema freeze", "status": "Done", "story_points": 8},
            {"key": "PROJ-402", "summary": "ETL cutover dry-run", "status": "Done", "story_points": 13},
            {"key": "PROJ-403", "summary": "Backfill verification", "status": "In Progress", "story_points": 8},
            {"key": "PROJ-404", "summary": "Legacy BI deprecation", "status": "Blocked", "story_points": 5},
            {"key": "PROJ-405", "summary": "Cost model review", "status": "To Do", "story_points": 3},
        ],
        "milestone_status": "Big-bang cutover window scheduled Dec 2",
        "risks_mitigations": (
            "- Backfill variance vs legacy (HIGH): dual-run reconciliation for two weeks\n"
            "- Legacy BI deprecation pushback (MED): exec alignment meeting booked"
        ),
        "key_wins": (
            "- Schema frozen without breaking changes\n"
            "- Dry-run cutover completed in 41 minutes\n"
            "- Query cost down 22% vs legacy"
        ),
    },
]


@app.get("/rest/api/3/search")
def search() -> dict:
    """Return one randomly selected sprint dataset (issues + narrative fields)."""
    data = random.choice(DATASETS)
    return {**data, "total": len(data["issues"])}
