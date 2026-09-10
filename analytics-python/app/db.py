"""PostgreSQL access for the analytics service. Reads the same tables the Java API writes."""
import os
from sqlalchemy import create_engine, text

DB_URL = os.getenv(
    "DB_URL_PY",
    "postgresql+psycopg2://planirovanie:planirovanie@localhost:5432/planirovanie",
)
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)


def _rows(sql):
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql))]


def load_state():
    """Assemble a dict shaped like the front-end ST object from the relational tables."""
    pr = _rows("SELECT * FROM params WHERE id = 1")
    p = pr[0] if pr else {}
    st = {
        "params": {
            "name": p.get("name"), "start": p.get("start_date"), "sprintDays": p.get("sprint_days"),
            "focus": p.get("focus"), "today": p.get("today_date"), "goal": p.get("goal"),
            "sprints": p.get("sprints") or 11,
        },
        "budget": {"rate": p.get("budget_rate"), "total": p.get("budget_total")},
        "ttmTarget": p.get("ttm_target") or 15,
        "team": [{"name": r["name"], "role": r["role"], "avail": r["avail"], "absent": r["absent"]}
                 for r in _rows("SELECT * FROM team ORDER BY ord")],
        "tasks": [{"id": r["task_id"], "title": r["title"], "role": r["role"], "type": r["type"],
                   "est": r["est"], "status": r["status"], "sprint": r["sprint"], "dep": r["dep"],
                   "started": r["started"], "done": r["done"]}
                  for r in _rows("SELECT * FROM tasks ORDER BY ord")],
        "releases": [{"id": r["rel_id"], "name": r["name"], "sfrom": r["sfrom"], "sto": r["sto"], "status": r["status"]}
                     for r in _rows("SELECT * FROM releases ORDER BY ord")],
        "milestones": [{"id": r["ms_id"], "name": r["name"], "sprint": r["sprint"], "status": r["status"], "rel": r["rel"]}
                       for r in _rows("SELECT * FROM milestones ORDER BY ord")],
        "bugs": [{"id": r["bug_id"], "sprint": r["sprint"], "sev": r["sev"], "status": r["status"], "task": r["task"]}
                 for r in _rows("SELECT * FROM bugs ORDER BY ord")],
        "calendar": [{"date": r["cdate"], "name": r["name"]} for r in _rows("SELECT * FROM calendar ORDER BY ord")],
        "rice": [{"id": r["rice_id"], "name": r["name"], "reach": r["reach"], "impact": r["impact"],
                  "conf": r["conf"], "effort": r["effort"]} for r in _rows("SELECT * FROM rice ORDER BY ord")],
        "deps": [{"id": r["dep_id"], "item": r["item"], "stream": r["stream"], "dir": r["dir"],
                  "status": r["status"], "task": r["task"]} for r in _rows("SELECT * FROM deps ORDER BY ord")],
        "dod": [{"crit": r["crit"], "done": r["done"]} for r in _rows("SELECT * FROM dod ORDER BY ord")],
    }
    return st


def ping():
    with engine.connect() as c:
        c.execute(text("SELECT 1"))
    return True
