# Frontend e2e / regression tests

End-to-end and functional tests for the `frontend/index.html` SPA, driven by
[Playwright](https://playwright.dev/python/). One command runs the **full regression
suite over all application functionality**.

## Run

```bash
pip install -r tests/frontend/requirements.txt
python -m playwright install chromium        # first time only (add --with-deps in CI)
python tests/frontend/run_e2e.py
```

Or via the Makefile:

```bash
make test-frontend        # frontend only
make test                 # java + python + frontend (full regression)
```

The script starts a local static server for `frontend/`, launches headless Chromium,
runs every check, prints a `PASS/FAIL/SKIP` line per test, and exits non-zero if any
test fails (so CI blocks the merge).

## What it covers

- **Every navigation section** — auto-discovered from the app's `NAV`, each section is
  activated and asserted to render without console errors.
- **Metrics engine** (`compute()`), **EDA report**, **data-quality checks**.
- **Kanban** multi-board role-routing, **release composition**, **whiteboard**.
- **Exports**: Excel workbook validity; **PPTX sprint report** builds and is *not*
  corrupt (regression guard for the `[Content_Types].xml` slideMaster bug — every
  content-type override must resolve to a real part).
- **Data**: `migrate()` idempotency, `save()` persistence, and the **permission gate**
  (a viewer cannot persist).
- **Support** section lists documents and excludes the admin guide.
- **Versioning**: `APP_VERSION` matches the changelog head.

## Adding a new feature → tests are (mostly) automatic

This is the project convention (see root `AGENTS.md`):

1. **A new section** added to `NAV` is **covered automatically** — the smoke loop
   discovers it and asserts it renders error-free. No test code to write.
2. **New logic** (a compute path, an export, an automation, a new data model) needs a
   **deep test**: add a `case('<area>: <behavior>', t_fn)` block in `run_e2e.py`
   following the existing pattern. Keep it data-tolerant (assert shape/ranges, not exact
   seed values) so it stays green as demo data evolves.
3. Run `make test-frontend` before committing; CI runs the whole suite on every push/PR.
