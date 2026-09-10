#!/usr/bin/env python3
"""Standalone functional test for the analytics engine (no database needed).
Runs compute() over data/seed.json and checks the numbers match the app.
Run: python analytics-python/tests/test_compute.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analytics-python"))

from app import compute as C  # noqa: E402


def main():
    st = json.load(open(ROOT / "data" / "seed.json", encoding="utf-8"))

    m = C.compute(st)
    assert m["closedSprints"] == 2, m["closedSprints"]
    assert abs(m["avgVelocity"] - 19.0) < 1e-6, m["avgVelocity"]
    assert abs(m["remaining"] - 61.0) < 1e-6, m["remaining"]
    assert len(m["sprints"]) == 11, len(m["sprints"])
    assert len(m["quarters"]) == 2, len(m["quarters"])

    d = C.deps_summary(st)
    assert d["total"] == 8 and d["blocked"] == 2 and d["inbound"] == 6, d

    r = C.rice_ranked(st)
    assert r[0]["id"] == "F-02" and r[0]["score"] == 480.0, r[0]
    assert r[0]["priority"] == "Высокий", r[0]

    b = C.burndown(st)
    assert b["scope"] == 107.0 and len(b["remaining"]) == 12, b["scope"]

    print("python analytics tests OK "
          f"(velocity={m['avgVelocity']}, health={m['health']}, "
          f"deps={d['total']}/{d['blocked']}, rice[0]={r[0]['id']}={r[0]['score']})")


if __name__ == "__main__":
    main()
