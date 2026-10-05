# -*- coding: utf-8 -*-
"""Regenerate the on-disk Excel export by driving the app's own exportXlsx().

Reusable across releases: it triggers the application's built-in export, so new
sheets added in the app appear automatically and the file is byte-identical to
what a user downloads via the «Данные → Excel» menu.

Usage:
    python scripts/deliverables/gen_xlsx.py [out_xlsx]

Default out_xlsx = <repo>/Планирование_спринта_PRO.xlsx . Requires: playwright.
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parents[2]
APP = (REPO / "frontend" / "index.html").as_uri()
DEST = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (REPO / "Планирование_спринта_PRO.xlsx")

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(accept_downloads=True)
    pg = ctx.new_page()
    pg.goto(APP)
    pg.wait_for_function("() => typeof exportXlsx === 'function' && typeof ST !== 'undefined'")
    pg.wait_for_timeout(400)
    with pg.expect_download() as di:
        pg.evaluate("()=>exportXlsx()")
    di.value.save_as(str(DEST))
    ctx.close(); b.close()
print("saved", DEST, DEST.stat().st_size, "bytes")
