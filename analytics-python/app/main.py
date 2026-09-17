"""FastAPI analytics service. Computes sprint metrics from PostgreSQL (read-only).

Data endpoints require the SAME bearer session token as the Java API (validated against the
shared app_sessions table), so analytics does not silently bypass application authentication.
Set ANALYTICS_AUTH_ENABLED=false only for local dev/tests. /analytics/health stays public.
"""
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import db
from . import compute as C

AUTH_ENABLED = os.getenv("ANALYTICS_AUTH_ENABLED", "true").lower() in ("1", "true", "yes", "on")
CORS_ORIGINS = [o.strip() for o in os.getenv("ANALYTICS_CORS_ORIGINS", "*").split(",") if o.strip()] or ["*"]

app = FastAPI(title="Планирование — сервис аналитики", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET"], allow_headers=["*"],
)


def require_auth(authorization: str = Header(default=None), x_auth_token: str = Header(default=None)):
    """Validate a bearer session token against the shared app_sessions table."""
    if not AUTH_ENABLED:
        return None
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_auth_token:
        token = x_auth_token.strip()
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        with db.engine.connect() as c:
            row = c.execute(text("SELECT expires_at FROM app_sessions WHERE token = :t"),
                            {"t": token}).fetchone()
    except Exception:
        raise HTTPException(status_code=503, detail="auth_unavailable")
    if row is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    exp = row[0]
    if exp is not None:
        if getattr(exp, "tzinfo", None) is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="session_expired")
    return token


@app.get("/analytics/health")
def health():
    try:
        db.ping()
        return {"status": "ok", "service": "python-analytics", "db": "up"}
    except Exception as e:  # noqa: BLE001
        return {"status": "degraded", "service": "python-analytics", "db": "down", "error": str(e)}


@app.get("/analytics/metrics", dependencies=[Depends(require_auth)])
def metrics():
    return C.compute(db.load_state())


@app.get("/analytics/rice", dependencies=[Depends(require_auth)])
def rice():
    return {"items": C.rice_ranked(db.load_state())}


@app.get("/analytics/burndown", dependencies=[Depends(require_auth)])
def burndown():
    return C.burndown(db.load_state())


@app.get("/analytics/dependencies", dependencies=[Depends(require_auth)])
def dependencies():
    return C.deps_summary(db.load_state())
