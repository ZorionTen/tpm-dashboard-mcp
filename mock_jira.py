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
    return {"issues": ISSUES, "total": len(ISSUES)}
