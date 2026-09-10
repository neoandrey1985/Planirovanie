"""Analytics engine — Python port of the app's compute() logic, over data loaded from PostgreSQL."""
from datetime import date, timedelta


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def pdate(s):
    try:
        return date.fromisoformat(s) if s else None
    except (TypeError, ValueError):
        return None


def networkdays(a, b, holidays):
    c, d = 0, a
    while d <= b:
        if d.weekday() < 5 and d.isoformat() not in holidays:
            c += 1
        d += timedelta(days=1)
    return c


def qof(d):
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


def sprints_of(st):
    P = st.get("params", {})
    start = pdate(P.get("start")) or date(2026, 8, 3)
    today = pdate(P.get("today")) or date.today()
    N = int(P.get("sprints") or 11)
    focus = num(P.get("focus")) or 0.8
    hol = {h["date"] for h in st.get("calendar", []) if h.get("date")}
    team = st.get("team", [])
    tasks = st.get("tasks", [])
    sp = []
    for s in range(1, N + 1):
        a = start + timedelta(days=(s - 1) * 14)
        b = start + timedelta(days=(s - 1) * 14 + 11)
        wd = networkdays(a, b, hol)
        cap = sum((wd - num(m.get("absent"))) * num(m.get("avail")) * focus for m in team)
        plan = sum(num(t.get("est")) for t in tasks if int(t.get("sprint") or 0) == s)
        status = "Закрыт" if today > b else ("Активный" if today >= a else "Планируется")
        vel = (sum(num(t.get("est")) for t in tasks
                   if int(t.get("sprint") or 0) == s and t.get("status") == "Готово")
               if status == "Закрыт" else None)
        pct = (vel / plan) if (plan and vel is not None) else None
        sp.append({"s": s, "a": a, "b": b, "wd": wd, "cap": round(cap * 10) / 10,
                   "plan": plan, "vel": vel, "status": status, "pct": pct})
    return sp, start, today, N


def compute(st):
    sp, start, today, N = sprints_of(st)
    tasks = st.get("tasks", [])
    started = sum(1 for x in sp if today >= x["a"])
    cur = max(1, min(N, started)) if sp else 1
    closed = [x for x in sp if x["status"] == "Закрыт"]
    vels = [x["vel"] for x in closed if x["vel"] not in (None, 0)]
    avg_vel = sum(vels) / len(vels) if vels else 0
    dod = st.get("dod", [])
    dod_pct = (sum(1 for d in dod if d.get("done")) / len(dod)) if dod else 0

    def rel_date(r):
        idx = int(r["sto"]) - 1
        return sp[idx]["b"] if 0 <= idx < len(sp) else None

    ttmv = []
    for t in tasks:
        r = next((r for r in st.get("releases", [])
                  if int(r["sfrom"]) <= int(t.get("sprint") or 0) <= int(r["sto"])), None)
        if r and t.get("started"):
            rd = rel_date(r)
            sd = pdate(t["started"])
            if rd and sd:
                ttmv.append((rd - sd).days)
    ttm_avg = sum(ttmv) / len(ttmv) if ttmv else 0

    bugs = st.get("bugs", [])
    bugs_found = len(bugs)
    bugs_closed = sum(1 for b in bugs if b.get("status") == "Закрыт")
    bugs_open = bugs_found - bugs_closed
    dre = bugs_closed / bugs_found if bugs_found else 0
    qual_norm = 1 - min(1, bugs_open / 5)
    avg_pct = (sum((x["pct"] or 0) for x in closed) / len(closed)) if closed else 0
    health = (min(1, avg_pct) + dod_pct + qual_norm) / 3
    remain = sum(x["plan"] for x in sp if x["status"] != "Закрыт")

    rate = num(st.get("budget", {}).get("rate")) or 8000
    cum = 0
    for x in sp:
        x["cost"] = round(x["cap"] * rate)
        cum += x["cost"]
        x["cum"] = cum

    qmap, qord = {}, []
    for x in sp:
        q = qof(x["a"])
        if q not in qmap:
            qmap[q] = {"q": q, "n": 0, "cap": 0.0, "plan": 0.0, "vel": 0.0, "hasVel": False}
            qord.append(q)
        o = qmap[q]
        o["n"] += 1
        o["cap"] += x["cap"]
        o["plan"] += x["plan"]
        if x["vel"] is not None:
            o["vel"] += x["vel"]
            o["hasVel"] = True
    quarters = []
    for k in qord:
        o = qmap[k]
        o["load"] = o["plan"] / o["cap"] if o["cap"] else 0
        o["pct"] = (o["vel"] / o["plan"]) if (o["hasVel"] and o["plan"]) else None
        o["cap"] = round(o["cap"] * 10) / 10
        quarters.append(o)

    mean = sum(vels) / len(vels) if vels else 0
    sd = (sum((v - mean) ** 2 for v in vels) / (len(vels) - 1)) ** 0.5 if len(vels) > 1 else 0
    cv = sd / mean if mean else 0
    done_tasks = sum(1 for t in tasks if t.get("status") == "Готово")
    throughput = done_tasks / len(closed) if closed else 0
    forecast = remain / avg_vel if avg_vel else None

    def ser(x):
        return {**{k: v for k, v in x.items() if k not in ("a", "b")},
                "start": x["a"].isoformat(), "end": x["b"].isoformat()}

    return {
        "sprints": [ser(x) for x in sp],
        "current": cur,
        "avgVelocity": round(avg_vel, 2),
        "closedSprints": len(closed),
        "dodPct": round(dod_pct, 3),
        "ttmAvg": round(ttm_avg, 2),
        "ttmTarget": st.get("ttmTarget", 15),
        "bugsFound": bugs_found, "bugsClosed": bugs_closed, "bugsOpen": bugs_open,
        "dre": round(dre, 3),
        "health": round(health, 3),
        "remaining": round(remain, 1),
        "quarters": quarters,
        "predictability": round(1 - min(1, cv), 3),
        "cv": round(cv, 3),
        "throughput": round(throughput, 2),
        "forecastSprints": round(forecast, 2) if forecast is not None else None,
    }


def rice_conf(v):
    s = str(v)
    return num(s.replace("%", "")) / 100 if "%" in s else num(v)


def rice_score(r):
    eff = num(r.get("effort"))
    return (num(r.get("reach")) * num(r.get("impact")) * rice_conf(r.get("conf")) / eff) if eff else 0


def rice_ranked(st):
    items = [{"id": r.get("id"), "name": r.get("name"), "reach": num(r.get("reach")),
              "impact": num(r.get("impact")), "confidence": rice_conf(r.get("conf")),
              "effort": num(r.get("effort")), "score": round(rice_score(r), 1)}
             for r in st.get("rice", [])]
    items.sort(key=lambda x: x["score"], reverse=True)
    mx = items[0]["score"] if items else 1
    for i, it in enumerate(items):
        it["rank"] = i + 1
        it["priority"] = ("Высокий" if it["score"] >= 0.6 * mx
                          else "Средний" if it["score"] >= 0.3 * mx else "Низкий")
    return items


def burndown(st):
    sp, *_ = sprints_of(st)
    scope = sum(num(t.get("est")) for t in st.get("tasks", []))
    cats = ["С0"] + [f"С{x['s']}" for x in sp]
    cum, remaining, done_cum, stop = 0, [scope], [0], False
    for x in sp:
        if x["vel"] is None or stop:
            stop = True
            remaining.append(None)
            done_cum.append(None)
        else:
            cum += x["vel"]
            remaining.append(max(0, scope - cum))
            done_cum.append(cum)
    n = len(cats)
    ideal = [scope * (1 - i / (n - 1)) for i in range(n)] if n > 1 else [scope]
    return {"labels": cats, "scope": scope, "remaining": remaining, "done": done_cum, "ideal": ideal}


def deps_summary(st):
    deps = st.get("deps", [])
    by_status, by_stream = {}, {}
    for d in deps:
        by_status[d.get("status")] = by_status.get(d.get("status"), 0) + 1
        by_stream[d.get("stream")] = by_stream.get(d.get("stream"), 0) + 1
    blocked = sum(1 for d in deps if d.get("status") in ("Заблокировано", "Просрочено"))
    inbound = sum(1 for d in deps if d.get("dir") == "Мы зависим")
    return {
        "total": len(deps), "blocked": blocked, "inbound": inbound, "outbound": len(deps) - inbound,
        "byStatus": by_status, "byStream": by_stream,
        "critical": [d for d in deps if d.get("status") in ("Заблокировано", "Просрочено")],
    }
