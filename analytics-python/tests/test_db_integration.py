#!/usr/bin/env python3
"""Integration test for the DB access layer (app/db.py) against a REAL PostgreSQL.

Spins up postgres via testcontainers, applies the Flyway V1 migration (schema + seed),
then verifies db.load_state() reads every collection with the right column mapping and
that compute() agrees. This is the check that db.py's SQL matches the real schema.

Requires Docker. Run: python analytics-python/tests/test_db_integration.py
"""
import importlib
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analytics-python"))
MIGRATION = ROOT / "backend-java" / "src" / "main" / "resources" / "db" / "migration" / "V1__initial_schema_and_seed.sql"


def main():
    from testcontainers.postgres import PostgresContainer
    from sqlalchemy import create_engine

    sql = MIGRATION.read_text(encoding="utf-8")
    with PostgresContainer("postgres:16") as pg:
        url = pg.get_connection_url()  # postgresql+psycopg2://.../test

        eng = create_engine(url)
        raw = eng.raw_connection()
        try:
            cur = raw.cursor()
            cur.execute(sql)  # psycopg2 executes the whole multi-statement migration
            raw.commit()
        finally:
            raw.close()

        os.environ["DB_URL_PY"] = url
        from app import db as dbmod
        importlib.reload(dbmod)  # rebuild the engine against the container URL

        st = dbmod.load_state()
        assert len(st["tasks"]) == 20 and st["tasks"][0]["id"] == "T-01", st["tasks"][:1]
        assert len(st["team"]) == 13, len(st["team"])
        assert len(st["deps"]) == 8 and st["deps"][0]["id"] == "D-01", st["deps"][:1]
        assert len(st["rice"]) == 10, len(st["rice"])
        assert st["calendar"][0]["date"] == "2026-11-04", st["calendar"][:1]
        assert st["params"]["sprints"] == 11 and st["budget"]["rate"] == 8000, st["params"]

        from app import compute as C
        m = C.compute(st)
        assert m["avgVelocity"] == 19.0 and m["closedSprints"] == 2, m

        print("db.py integration test OK "
              f"(tasks={len(st['tasks'])}, team={len(st['team'])}, deps={len(st['deps'])}, "
              f"velocity={m['avgVelocity']})")


if __name__ == "__main__":
    main()
