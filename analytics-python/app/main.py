"""FastAPI analytics service. Computes sprint metrics from PostgreSQL (read-only)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from . import compute as C

app = FastAPI(title="Планирование — сервис аналитики", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/analytics/health")
def health():
    try:
        db.ping()
        return {"status": "ok", "service": "python-analytics", "db": "up"}
    except Exception as e:  # noqa: BLE001
        return {"status": "degraded", "service": "python-analytics", "db": "down", "error": str(e)}


@app.get("/analytics/metrics")
def metrics():
    return C.compute(db.load_state())


@app.get("/analytics/rice")
def rice():
    return {"items": C.rice_ranked(db.load_state())}


@app.get("/analytics/burndown")
def burndown():
    return C.burndown(db.load_state())


@app.get("/analytics/dependencies")
def dependencies():
    return C.deps_summary(db.load_state())
