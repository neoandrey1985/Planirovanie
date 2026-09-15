#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the Flyway migration (schema + seed) from data/seed.json.
Output: backend-java/src/main/resources/db/migration/V1__initial_schema_and_seed.sql
Run: python scripts/gen_initsql.py"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "backend-java" / "src" / "main" / "resources" / "db" / "migration" / "V1__initial_schema_and_seed.sql"
SEED = json.load(open(ROOT / "data" / "seed.json", encoding="utf-8"))


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


out = []
out.append("-- Flyway V1: schema + seed for Планирование спринтов (PostgreSQL).")
out.append("-- Auto-generated — regenerate with: python scripts/gen_initsql.py")
out.append("-- Source of truth for the Java (JPA) and Python (SQLAlchemy) services.\n")

DDL = """
CREATE TABLE IF NOT EXISTS params (
  id           INT PRIMARY KEY DEFAULT 1,
  name         TEXT, start_date TEXT, sprint_days INT, focus DOUBLE PRECISION,
  today_date   TEXT, goal TEXT, sprints INT,
  budget_rate  DOUBLE PRECISION, budget_total DOUBLE PRECISION, ttm_target INT
);
CREATE TABLE IF NOT EXISTS dod        (id SERIAL PRIMARY KEY, crit TEXT, done BOOLEAN, ord INT);
CREATE TABLE IF NOT EXISTS team       (id SERIAL PRIMARY KEY, name TEXT, role TEXT, avail DOUBLE PRECISION, absent DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS tasks      (pk SERIAL PRIMARY KEY, task_id TEXT, title TEXT, assignee TEXT, role TEXT, type TEXT, est DOUBLE PRECISION, status TEXT, sprint INT, dep TEXT, started TEXT, done TEXT, added BOOLEAN, ord INT);
CREATE TABLE IF NOT EXISTS releases   (pk SERIAL PRIMARY KEY, rel_id TEXT, name TEXT, sfrom INT, sto INT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS milestones (pk SERIAL PRIMARY KEY, ms_id TEXT, name TEXT, sprint INT, status TEXT, rel TEXT, ord INT);
CREATE TABLE IF NOT EXISTS tech_debt  (pk SERIAL PRIMARY KEY, td_id TEXT, descr TEXT, area TEXT, type TEXT, impact TEXT, est DOUBLE PRECISION, status TEXT, created INT, paid INT, ord INT);
CREATE TABLE IF NOT EXISTS risks      (pk SERIAL PRIMARY KEY, name TEXT, p INT, i INT, mit TEXT, owner TEXT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS bugs       (pk SERIAL PRIMARY KEY, bug_id TEXT, descr TEXT, task TEXT, sprint INT, sev TEXT, status TEXT, time_h DOUBLE PRECISION, reopened BOOLEAN, cause TEXT, ord INT);
CREATE TABLE IF NOT EXISTS calendar   (id SERIAL PRIMARY KEY, cdate TEXT, name TEXT, ord INT);
CREATE TABLE IF NOT EXISTS retro      (id SERIAL PRIMARY KEY, sprint INT, well TEXT, improve TEXT, action TEXT, owner TEXT, due TEXT, status TEXT, votes DOUBLE PRECISION, rformat TEXT, ord INT);
CREATE TABLE IF NOT EXISTS mood       (pk SERIAL PRIMARY KEY, mood_id TEXT, sprint INT, mood DOUBLE PRECISION, note TEXT, ord INT);
CREATE TABLE IF NOT EXISTS kudos      (pk SERIAL PRIMARY KEY, kudos_id TEXT, sprint INT, from_who TEXT, to_who TEXT, reason TEXT, ord INT);
CREATE TABLE IF NOT EXISTS experiments(pk SERIAL PRIMARY KEY, exp_id TEXT, sprint INT, hypothesis TEXT, action TEXT, metric TEXT, result TEXT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS radar      (pk SERIAL PRIMARY KEY, radar_id TEXT, axis TEXT, score DOUBLE PRECISION, prev DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS rice       (pk SERIAL PRIMARY KEY, rice_id TEXT, task TEXT, name TEXT, reach DOUBLE PRECISION, impact DOUBLE PRECISION, conf TEXT, effort DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS moscow     (pk SERIAL PRIMARY KEY, ms_id TEXT, task TEXT, name TEXT, category TEXT, note TEXT, ord INT);
CREATE TABLE IF NOT EXISTS faq        (pk SERIAL PRIMARY KEY, faq_id TEXT, category TEXT, question TEXT, answer TEXT, ord INT);
CREATE TABLE IF NOT EXISTS grooming   (pk SERIAL PRIMARY KEY, grm_id TEXT, task TEXT, gdate TEXT, item TEXT, action TEXT, est DOUBLE PRECISION, ready TEXT, owner TEXT, notes TEXT, ord INT);
CREATE TABLE IF NOT EXISTS demo       (pk SERIAL PRIMARY KEY, demo_id TEXT, sprint INT, ddate TEXT, item TEXT, presenter TEXT, stakeholders TEXT, feedback TEXT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS daily      (pk SERIAL PRIMARY KEY, daily_id TEXT, ddate TEXT, sprint INT, participant TEXT, yesterday TEXT, today TEXT, blocker TEXT, ord INT);
CREATE TABLE IF NOT EXISTS vacation   (pk SERIAL PRIMARY KEY, vac_id TEXT, member TEXT, vtype TEXT, dfrom TEXT, dto TEXT, days DOUBLE PRECISION, status TEXT, notes TEXT, ord INT);
CREATE TABLE IF NOT EXISTS birthdays  (pk SERIAL PRIMARY KEY, bd_id TEXT, member TEXT, bdate TEXT, role TEXT, notes TEXT, ord INT);
CREATE TABLE IF NOT EXISTS deps       (pk SERIAL PRIMARY KEY, dep_id TEXT, item TEXT, type TEXT, task TEXT, stream TEXT, dir TEXT, descr TEXT, sprint INT, status TEXT, owner TEXT, risk TEXT, ord INT);
CREATE TABLE IF NOT EXISTS okr        (id SERIAL PRIMARY KEY, q TEXT, obj TEXT, kr TEXT, target DOUBLE PRECISION, cur DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS app_meta   (id INT PRIMARY KEY DEFAULT 1, version BIGINT DEFAULT 1);
"""
out.append(DDL.strip() + "\n")


def rows(table, cols, data, mapper):
    out.append(f"\n-- {table}")
    for i, item in enumerate(data):
        vals = mapper(item, i)
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(q(v) for v in vals)});")


p = SEED.get("params", {})
b = SEED.get("budget", {})
out.append("\n-- params (single row)")
out.append("INSERT INTO params (id,name,start_date,sprint_days,focus,today_date,goal,sprints,budget_rate,budget_total,ttm_target) VALUES ("
    + ",".join(q(v) for v in [1, p.get("name"), p.get("start"), p.get("sprintDays"), p.get("focus"),
      p.get("today"), p.get("goal"), p.get("sprints", 11), b.get("rate", 8000), b.get("total", 8000000),
      SEED.get("ttmTarget", 15)]) + ");")

rows("dod", ["crit", "done", "ord"], SEED.get("dod", []), lambda d, i: [d.get("crit"), d.get("done"), i])
rows("team", ["name", "role", "avail", "absent", "ord"], SEED.get("team", []),
     lambda d, i: [d.get("name"), d.get("role"), d.get("avail"), d.get("absent"), i])
rows("tasks", ["task_id", "title", "assignee", "role", "type", "est", "status", "sprint", "dep", "started", "done", "added", "ord"],
     SEED.get("tasks", []), lambda d, i: [d.get("id"), d.get("title"), d.get("assignee"), d.get("role"), d.get("type"),
      d.get("est"), d.get("status"), d.get("sprint"), d.get("dep"), d.get("started"), d.get("done"), d.get("added"), i])
rows("releases", ["rel_id", "name", "sfrom", "sto", "status", "ord"], SEED.get("releases", []),
     lambda d, i: [d.get("id"), d.get("name"), d.get("sfrom"), d.get("sto"), d.get("status"), i])
rows("milestones", ["ms_id", "name", "sprint", "status", "rel", "ord"], SEED.get("milestones", []),
     lambda d, i: [d.get("id"), d.get("name"), d.get("sprint"), d.get("status"), d.get("rel"), i])
rows("tech_debt", ["td_id", "descr", "area", "type", "impact", "est", "status", "created", "paid", "ord"], SEED.get("techDebt", []),
     lambda d, i: [d.get("id"), d.get("desc"), d.get("area"), d.get("type"), d.get("impact"), d.get("est"), d.get("status"), d.get("created"), d.get("paid"), i])
rows("risks", ["name", "p", "i", "mit", "owner", "status", "ord"], SEED.get("risks", []),
     lambda d, i: [d.get("name"), d.get("p"), d.get("i"), d.get("mit"), d.get("owner"), d.get("status"), i])
rows("bugs", ["bug_id", "descr", "task", "sprint", "sev", "status", "time_h", "reopened", "cause", "ord"], SEED.get("bugs", []),
     lambda d, i: [d.get("id"), d.get("desc"), d.get("task"), d.get("sprint"), d.get("sev"), d.get("status"), d.get("time"), d.get("reopened"), d.get("cause"), i])
rows("calendar", ["cdate", "name", "ord"], SEED.get("calendar", []),
     lambda d, i: [(d.get("date") if isinstance(d, dict) else d), (d.get("name") if isinstance(d, dict) else ""), i])
rows("mood", ["mood_id", "sprint", "mood", "note", "ord"], SEED.get("mood", []),
     lambda d, i: [d.get("id"), d.get("sprint"), d.get("mood"), d.get("note"), i])
rows("kudos", ["kudos_id", "sprint", "from_who", "to_who", "reason", "ord"], SEED.get("kudos", []),
     lambda d, i: [d.get("id"), d.get("sprint"), d.get("from"), d.get("to"), d.get("reason"), i])
rows("experiments", ["exp_id", "sprint", "hypothesis", "action", "metric", "result", "status", "ord"], SEED.get("experiments", []),
     lambda d, i: [d.get("id"), d.get("sprint"), d.get("hypothesis"), d.get("action"), d.get("metric"), d.get("result"), d.get("status"), i])
rows("radar", ["radar_id", "axis", "score", "prev", "ord"], SEED.get("radar", []),
     lambda d, i: [d.get("id"), d.get("axis"), d.get("score"), d.get("prev"), i])
rows("retro", ["sprint", "well", "improve", "action", "owner", "due", "status", "votes", "rformat", "ord"], SEED.get("retro", []),
     lambda d, i: [d.get("sprint"), d.get("well"), d.get("improve"), d.get("action"), d.get("owner"), d.get("due"), d.get("status"), d.get("votes"), d.get("format"), i])
rows("rice", ["rice_id", "task", "name", "reach", "impact", "conf", "effort", "ord"], SEED.get("rice", []),
     lambda d, i: [d.get("id"), d.get("task"), d.get("name"), d.get("reach"), d.get("impact"), d.get("conf"), d.get("effort"), i])
rows("moscow", ["ms_id", "task", "name", "category", "note", "ord"], SEED.get("moscow", []),
     lambda d, i: [d.get("id"), d.get("task"), d.get("name"), d.get("category"), d.get("note"), i])
rows("faq", ["faq_id", "category", "question", "answer", "ord"], SEED.get("faq", []),
     lambda d, i: [d.get("id"), d.get("category"), d.get("q"), d.get("a"), i])
rows("grooming", ["grm_id", "task", "gdate", "item", "action", "est", "ready", "owner", "notes", "ord"], SEED.get("grooming", []),
     lambda d, i: [d.get("id"), d.get("task"), d.get("date"), d.get("item"), d.get("action"), d.get("est"), d.get("ready"), d.get("owner"), d.get("notes"), i])
rows("demo", ["demo_id", "sprint", "ddate", "item", "presenter", "stakeholders", "feedback", "status", "ord"], SEED.get("demo", []),
     lambda d, i: [d.get("id"), d.get("sprint"), d.get("date"), d.get("item"), d.get("presenter"), d.get("stakeholders"), d.get("feedback"), d.get("status"), i])
rows("daily", ["daily_id", "ddate", "sprint", "participant", "yesterday", "today", "blocker", "ord"], SEED.get("daily", []),
     lambda d, i: [d.get("id"), d.get("date"), d.get("sprint"), d.get("participant"), d.get("yesterday"), d.get("today"), d.get("blocker"), i])
rows("vacation", ["vac_id", "member", "vtype", "dfrom", "dto", "days", "status", "notes", "ord"], SEED.get("vacation", []),
     lambda d, i: [d.get("id"), d.get("member"), d.get("type"), d.get("from"), d.get("to"), d.get("days"), d.get("status"), d.get("notes"), i])
rows("birthdays", ["bd_id", "member", "bdate", "role", "notes", "ord"], SEED.get("birthdays", []),
     lambda d, i: [d.get("id"), d.get("member"), d.get("date"), d.get("role"), d.get("notes"), i])
rows("deps", ["dep_id", "item", "type", "task", "stream", "dir", "descr", "sprint", "status", "owner", "risk", "ord"], SEED.get("deps", []),
     lambda d, i: [d.get("id"), d.get("item"), d.get("type"), d.get("task"), d.get("stream"), d.get("dir"), d.get("desc"), d.get("sprint"), d.get("status"), d.get("owner"), d.get("risk"), i])

OKR = SEED.get("okr") or [
    {"q": "Q3 2026", "obj": "Запустить подписочную модель", "kr": "Готовность MVP чекаута, %", "target": 100, "cur": 70},
    {"q": "Q3 2026", "obj": "Запустить подписочную модель", "kr": "Интеграция оплаты, %", "target": 100, "cur": 60},
    {"q": "Q3 2026", "obj": "Обеспечить качество релиза", "kr": "Покрытие автотестами, %", "target": 80, "cur": 45},
    {"q": "Q4 2026", "obj": "Масштабировать на площадки", "kr": "Подключено площадок, шт", "target": 20, "cur": 6},
]
rows("okr", ["q", "obj", "kr", "target", "cur", "ord"], OKR,
     lambda d, i: [d.get("q"), d.get("obj"), d.get("kr"), d.get("target"), d.get("cur"), i])

out.append("\n-- meta")
out.append("INSERT INTO app_meta (id, version) VALUES (1, 1);")

OUT.parent.mkdir(parents=True, exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
print(OUT.name, "written:", sum(1 for line in out if line.startswith("INSERT")), "INSERTs")
