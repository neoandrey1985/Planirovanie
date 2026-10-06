# -*- coding: utf-8 -*-
"""Copy the Support-section deliverables from the repo root into frontend/docs/.

The app's «Support» section serves documents from frontend/docs/ (see SUPPORT_DOCS in
frontend/index.html). Deliverable generators write to the repo ROOT, so after regenerating
run this to keep the served copies in sync. Only the files Support links to are copied.

Usage: python scripts/deliverables/sync_served_docs.py
"""
import pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEST = ROOT / "frontend" / "docs"
DEST.mkdir(parents=True, exist_ok=True)

# Must match SUPPORT_DOCS[].f in frontend/index.html.
SERVED = [
    "Руководство_пользователя_Планирование_спринта_PRO.docx",
    "Иллюстрированное_описание_Планирование_спринта_PRO.docx",
    "Презентация_приложения.pptx",
    "Обзор_приложения.mp4",
]

for f in SERVED:
    src = ROOT / f
    if not src.exists():
        print("MISSING in root:", f)
        continue
    shutil.copyfile(src, DEST / f)
    print("synced:", f, src.stat().st_size, "bytes")
print("done ->", DEST)
