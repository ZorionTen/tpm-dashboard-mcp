"""Mock Jira REST API — faithful v3 subset on a live, randomly-evolving board. Port 8000.

Endpoints:
  GET /rest/api/3/search?jql=...&fields=...&startAt=&maxResults=   Jira-shaped search
  GET /rest/api/3/issue/{key}                                       single issue
  GET /rest/api/3/myself                                            current user
  GET /rest/agile/1.0/sprint                                        sprints
  GET /rest/agile/1.0/sprint/{id}/issue                             sprint issues

The ACTIVE sprint's issues evolve on every search: statuses transition at
random (work happens between calls) and story points jitter — so metrics move.
Auth headers are accepted and ignored (prototype — no credentials).
"""
import random
import re
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Mock Jira", version="3.0")

STAT_CAT = {"To Do": "new", "In Progress": "indeterminate", "Blocked": "indeterminate", "Done": "done"}
ASSIGNEES = ["Alex Kim", "Sara Lindqvist", "David Chen", "Elena Petrova", "Marcus Vance"]
PRIORITIES = ["Highest", "High", "Medium", "Low"]

# Four sprints; the last one is active. Each sprint's issues come from the
# original demo datasets. goal == the dashboard's milestone status.
SPRINTS = [
    {"id": 21, "name": "Sprint 21", "state": "closed", "start": "2026-10-06", "end": "2026-10-19",
     "goal": "Payments certification60% complete, gate review Nov 21"},
    {"id": 22, "name": "Sprint 22", "state": "closed", "start": "2026-10-07", "end": "2026-10-20",
     "goal": "Closed beta with 200 users starts Nov 18"},
    {"id": 23, "name": "Sprint 23", "state": "closed", "start": "2026-10-21", "end": "2026-11-03",
     "goal": "Big-bang cutover window scheduled Dec 2"},
    {"id": 24, "name": "Sprint 24", "state": "active", "start": "2026-10-21", "end": "2026-11-04",
     "goal": "Authentication & Login API on track for the Nov 14 release"},
]

BACKLOG = {  # sprint_id -> [(key, summary, status, points)]
    21: [("PROJ-201", "Rate limiter rollout", "Done", 3), ("PROJ-202", "Vendor sandbox re-certification", "Done", 5),
         ("PROJ-203", "Checkout retry logic", "In Progress", 8), ("PROJ-204", "Fraud rules engine integration", "Blocked", 13),
         ("PROJ-205", "Rollout docs refresh", "To Do", 2)],
    22: [("PROJ-301", "Push notification service", "Done", 5), ("PROJ-302", "Offline cache layer", "Done", 8),
         ("PROJ-303", "Beta feedback triage", "Done", 3), ("PROJ-304", "iOS build pipeline", "In Progress", 5),
         ("PROJ-305", "Analytics events audit", "To Do", 3)],
    23: [("PROJ-401", "Warehouse schema freeze", "Done", 8), ("PROJ-402", "ETL cutover dry-run", "Done", 13),
         ("PROJ-403", "Backfill verification", "In Progress", 8), ("PROJ-404", "Legacy BI deprecation", "In Progress", 5),
         ("PROJ-405", "Cost model review", "To Do", 3)],
    24: [("PROJ-101", "Design auth flow", "Done", 5), ("PROJ-102", "Implement login API", "Done", 8),
         ("PROJ-103", "Dashboard widgets", "In Progress", 8), ("PROJ-104", "Payments integration blocked by vendor", "Blocked", 5),
         ("PROJ-105", "Write onboarding docs", "To Do", 3)],
}

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+0000")

ISSUES = []
_next_id = 10001
for _sid, _items in BACKLOG.items():
    for _i, (_key, _summary, _status, _pts) in enumerate(_items):
        ISSUES.append({
            "id": str(_next_id), "key": _key, "sprint_id": _sid,
            "summary": _summary, "status": _status, "points": _pts,
            "priority": random.choice(PRIORITIES), "assignee": random.choice(ASSIGNEES),
            "labels": [], "created": "2026-10-20T09:00:00.000+0000", "updated": _now(),
            "issuetype": random.choice(["Story", "Task"]),
        })
        _next_id += 1

def _sprint(sid: int) -> dict:
    s = next(x for x in SPRINTS if x["id"] == sid)
    return {"id": s["id"], "name": s["name"], "state": s["state"],
            "startDate": s["start"], "endDate": s["end"], "goal": s["goal"]}

def _issue_json(it: dict) -> dict:
    return {
        "id": it["id"], "key": it["key"],
        "self": f"http://127.0.0.1:8000/rest/api/3/issue/{it['id']}",
        "fields": {
            "summary": it["summary"],
            "status": {"name": it["status"],
                       "statusCategory": {"key": STAT_CAT[it["status"]], "name": STAT_CAT[it["status"]].title()}},
            "priority": {"name": it["priority"]},
            "assignee": {"displayName": it["assignee"], "accountId": it["assignee"].lower().replace(" ", "_")},
            "reporter": {"displayName": "Zaid Rahman", "accountId": "zaid"},
            "labels": it["labels"],
            "issuetype": {"name": it["issuetype"], "id": "10002"},
            "project": {"key": "PROJ", "name": "Platform Delivery"},
            "created": it["created"], "updated": it["updated"],
            "customfield_10016": it["points"],
            "sprint": _sprint(it["sprint_id"]),
        },
    }

# --- live board: random evolution of the active sprint on every search ---
TRANSITIONS = [("To Do", "In Progress", 0.28), ("In Progress", "Done", 0.22),
               ("In Progress", "Blocked", 0.07), ("Blocked", "In Progress", 0.18)]

def _evolve() -> None:
    active = [it for it in ISSUES if it["sprint_id"] == 24]
    if active and all(i["status"] == "Done" for i in active):
        # sprint completed — the next one starts, so metrics keep moving forever
        for i in active:
            i["status"] = random.choices(["To Do", "In Progress", "Blocked", "Done"], [4, 3, 1, 2])[0]
            i["updated"] = _now()
    for it in active:
        for src, dst, p in TRANSITIONS:
            if it["status"] == src and random.random() < p:
                it["status"] = dst
                it["updated"] = _now()
                break
        if it["status"] != "Done" and random.random() < 0.12:  # points jitter
            it["points"] = max(1, it["points"] + random.choice([-1, 1]))
            it["updated"] = _now()

# --- pragmatic JQL: AND/OR groups over: project, sprint, status, statusCategory, assignee, labels, text ---
def _clause_match(it: dict, clause: str) -> bool:
    c = clause.strip()
    m = re.match(r"(\w+)\s*(=|in|~)\s*(.+)", c, re.I)
    if not m:
        return True  # unknown clause → lenient ignore (realistic enough for the prototype)
    field, op, val = m.group(1).lower(), m.group(2).lower(), m.group(3).strip().strip('"')
    if field == "sprint":
        if "opensprints" in val.lower().replace(" ", ""):
            return it["sprint_id"] == 24
        return val.isdigit() and int(val) == it["sprint_id"] or val == _sprint(it["sprint_id"])["name"]
    if field == "project":
        return it["key"].startswith(val.upper())
    if field == "status":
        return it["status"].lower() == val.lower()
    if field == "statuscategory":
        return STAT_CAT[it["status"]] == val.lower()
    if field == "assignee":
        return "currentuser" in val.lower() or it["assignee"].lower() == val.lower()
    if field == "labels":
        return val in it["labels"]
    if field in ("text", "summary"):
        return val.lower() in it["summary"].lower()
    return True

def _search_filter(jql: str) -> list:
    q = re.split(r"\s+ORDER\s+BY\s+", jql, flags=re.I)[0].strip()
    groups = [re.split(r"\s+OR\s+", g, flags=re.I) for g in re.split(r"\s+AND\s+", q, flags=re.I) if g.strip()]
    return [it for it in ISSUES if all(any(_clause_match(it, c) for c in g) for g in groups)]

@app.get("/rest/api/3/search")
def search(jql: str = Query(""), fields: str = Query(""),
           startAt: int = Query(0), maxResults: int = Query(50)) -> dict:
    _evolve()  # the team did some work since your last call
    result = _search_filter(jql)
    return {"expand": "schema", "startAt": startAt, "maxResults": maxResults,
            "total": len(result), "issues": [_issue_json(i) for i in result[startAt:startAt + maxResults]]}

@app.get("/rest/api/3/issue/{key}")
def get_issue(key: str) -> dict:
    it = next((i for i in ISSUES if i["key"] == key.upper()), None)
    if not it:
        raise HTTPException(404, {"errorMessages": [], "errors": {"key": "Issue does not exist"}})
    return _issue_json(it)

@app.get("/rest/api/3/myself")
def myself() -> dict:
    return {"accountId": "zaid", "displayName": "Zaid Rahman", "active": True,
            "emailAddress": "zaid@example.com", "self": "http://127.0.0.1:8000/rest/api/3/myself"}

@app.get("/rest/agile/1.0/sprint")
def sprints(state: str = Query("")) -> dict:
    vals = [_sprint(s["id"]) | {"closedDate": None} for s in SPRINTS
            if not state or s["state"] == state]
    return {"maxResults": 50, "startAt": 0, "total": len(vals), "values": vals}

@app.get("/rest/agile/1.0/sprint/{sid}/issue")
def sprint_issues(sid: int) -> dict:
    if not any(s["id"] == sid for s in SPRINTS):
        raise HTTPException(404, {"errorMessages": ["Sprint does not exist"]})
    if sid == 24:
        _evolve()
    result = [i for i in ISSUES if i["sprint_id"] == sid]
    return {"expand": "schema", "startAt": 0, "maxResults": len(result),
            "total": len(result), "issues": [_issue_json(i) for i in result]}
