# -*- coding: utf-8 -*-
"""v1.57.0: Kanban — перетаскивание колонок за ⠿. Обновляет тексты документов/презентации и версию.
Снимок: capture_shots.py --only kanban → build/shots/kanban.jpg.
Идемпотентно. Запуск: python scripts/deliverables/release_v157_kanban_cols.py"""
import copy, glob, os, pathlib, docx
from docx.shared import Inches
from docx.text.paragraph import Paragraph
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

os.chdir(pathlib.Path(__file__).resolve().parents[2])
SH = pathlib.Path("build/shots")
P = "Планирование_спринта_PRO"
OLDV, NEWV = "1.56.1", "1.57.0"
REPL = [
    ("Администратор может создавать доски и добавлять колонки-статусы.",
     "Администратор может создавать доски, добавлять колонки-статусы и менять порядок колонок перетаскиванием за ⠿."),
    ("Администратор может создавать доски и добавлять колонки",
     "Администратор может создавать доски, добавлять колонки и менять их порядок перетаскиванием за ⠿"),
]
UG = ("Kanban: порядок колонок",
      "На Kanban-доске администратор меняет порядок колонок перетаскиванием за значок ⠿ в шапке колонки — в том числе сразу после добавления новой.",
      ["Ручка ⠿ появляется у администратора на досках со статусами (ролевые, «Все задачи», релизная).",
       "Перетащите колонку влево или вправо: порядок сохраняется в настройках доски и восстанавливается после перезагрузки.",
       "На доске «Состав релизов» колонки — это релизы; их порядок задаётся составом релизов, а не перетаскиванием колонок."],
      [("kanban.jpg", "Kanban-доска: ручки ⠿ для перестановки колонок")])
DESC = ("Kanban: перетаскивание колонок",
        "Администратор меняет порядок колонок на Kanban-доске перетаскиванием за ⠿; порядок сохраняется в настройках доски.")
SLIDE = ("🗃️", "Kanban: порядок колонок", "Перетаскивание колонок за ⠿.", "kanban.jpg", [
    "•  Ручка ⠿ в шапке каждой колонки.",
    "•  Порядок сохраняется в настройках доски.",
    "•  Работает и сразу после «＋ Колонка»."])
ANCHOR_SLIDE = "Что это"


def put_before(anchor, p):
    anchor._p.addprevious(p._p); return p


def add_pic(d, anchor, img, cap, width):
    if not (SH / img).exists():
        print("   ! нет снимка", img); return
    p = d.add_paragraph(); p.alignment = 1; p.add_run().add_picture(str(SH / img), width=Inches(width)); put_before(anchor, p)
    c = d.add_paragraph(cap); c.alignment = 1
    for r in c.runs: r.italic = True
    put_before(anchor, c)


def set_par(p, text):
    for r in p.runs[1:]: r.text = ""
    if p.runs: p.runs[0].text = text
    else: p.add_run(text)


def replace_in(d, a, b):
    n = 0
    for p in d.paragraphs:
        if a in p.text and b not in p.text:
            set_par(p, p.text.replace(a, b)); n += 1
    return n


def after(p, text):
    np_ = copy.deepcopy(p._p); p._p.addnext(np_); q = Paragraph(np_, p._parent); set_par(q, text); return q


def version(d):
    pars = list(d.paragraphs) + [p for t in d.tables for r in t.rows for c in r.cells for p in c.paragraphs] \
        + [p for s in d.sections for hf in (s.header, s.footer) for p in hf.paragraphs]
    n = 0
    for p in pars:
        if OLDV in p.text:
            for r in p.runs: r.text = r.text.replace(OLDV, NEWV)
            n += 1
        # also bump older head if present
        if "1.56.0" in p.text and NEWV not in p.text:
            for r in p.runs: r.text = r.text.replace("1.56.0", NEWV)
            n += 1
    return n


def next_heading(d, i):
    return next(p for p in d.paragraphs[i + 1:] if p.style.name.startswith("Heading"))


def heading(d, text, lvl="Heading 2"):
    return next(k for k, p in enumerate(d.paragraphs) if p.style.name == lvl and p.text.strip() == text)


def add_section(d, after_title, sec, width):
    title, text, bullets, pics = sec
    if any(p.text == title for p in d.paragraphs): return False
    try:
        anchor = next_heading(d, heading(d, after_title))
    except StopIteration:
        # fall back: append before last heading if exact title missing
        heads = [i for i, p in enumerate(d.paragraphs) if p.style.name.startswith("Heading 2")]
        if not heads: return False
        anchor = next_heading(d, heads[-1])
    put_before(anchor, d.add_paragraph(title, style="Heading 2")); put_before(anchor, d.add_paragraph(text))
    for b in bullets: put_before(anchor, d.add_paragraph(b, style="List Bullet"))
    for img, cap in pics: add_pic(d, anchor, img, cap, width)
    return True


def bump_docs():
    for fn in sorted(glob.glob("*.docx")) + sorted(glob.glob("Тестовая документация/*.docx")):
        d = docx.Document(fn); n = version(d); r = 0
        for a, b in REPL: r += replace_in(d, a, b)
        added = False
        if fn.startswith("Руководство_пользователя"):
            # try after a Kanban-related heading if present
            for cand in ("Kanban-доска", "Канбан", "Доски", "Планирование"):
                try:
                    added = add_section(d, cand, UG, 5.8); break
                except StopIteration:
                    continue
            if not added:
                # insert near end: before last H2
                heads = [(i, p.text) for i, p in enumerate(d.paragraphs) if p.style.name == "Heading 2"]
                if heads:
                    added = add_section(d, heads[-2][1] if len(heads) > 1 else heads[-1][1], UG, 5.8)
        if fn.startswith("Описание_") or fn.startswith("Иллюстрированное"):
            if not any(DESC[0] in p.text for p in d.paragraphs):
                heads = [p for p in d.paragraphs if p.style.name.startswith("Heading")]
                if heads:
                    anchor = heads[-1]
                    put_before(anchor, d.add_paragraph(DESC[0], style="Heading 2"))
                    put_before(anchor, d.add_paragraph(DESC[1]))
                    if fn.startswith("Иллюстрированное") and (SH / "kanban.jpg").exists():
                        add_pic(d, anchor, "kanban.jpg", "Kanban: ручки перестановки колонок", 5.8)
                    added = True
        d.save(fn); print(fn, "ver", n, "repl", r, "sec", added)


def clone_slide(prs, src):
    blank = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]
    slide = prs.slides.add_slide(blank)
    for shp in src.shapes:
        el = copy.deepcopy(shp.element); slide.shapes._spTree.insert_element_before(el, "p:extLst")
    return slide


def find_slide(prs, title):
    for i, s in enumerate(prs.slides):
        for shp in s.shapes:
            if shp.has_text_frame and title in shp.text_frame.text: return i, s
    return None, None


def set_shape_text(slide, idx, text):
    shapes = [s for s in slide.shapes if s.has_text_frame]
    if idx < len(shapes):
        tf = shapes[idx].text_frame
        if tf.paragraphs:
            if tf.paragraphs[0].runs: tf.paragraphs[0].runs[0].text = text
            else: tf.paragraphs[0].text = text


def bump_pptx():
    prs = Presentation("Презентация_приложения.pptx")
    # version on title-ish slides
    for s in prs.slides:
        for shp in s.shapes:
            if shp.has_text_frame and OLDV in shp.text_frame.text:
                for p in shp.text_frame.paragraphs:
                    for r in p.runs: r.text = r.text.replace(OLDV, NEWV)
    # add slide if missing
    if not any(SLIDE[1] in (shp.text_frame.text if shp.has_text_frame else "") for s in prs.slides for shp in s.shapes):
        ai, anchor = find_slide(prs, ANCHOR_SLIDE)
        src = anchor or prs.slides[min(2, len(prs.slides) - 1)]
        slide = clone_slide(prs, src)
        # try to fill first text shapes
        set_shape_text(slide, 0, SLIDE[0] + "  " + SLIDE[1])
        set_shape_text(slide, 1, SLIDE[2])
        # replace picture if possible
        img = SH / SLIDE[3]
        if img.exists():
            for shp in list(slide.shapes):
                if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    # leave existing; add new picture at similar box
                    slide.shapes.add_picture(str(img), shp.left, shp.top, width=shp.width)
                    break
            else:
                slide.shapes.add_picture(str(img), Inches(0.5), Inches(2.0), width=Inches(9))
        print("pptx: added slide", SLIDE[1])
    else:
        print("pptx: slide already present")
    prs.save("Презентация_приложения.pptx"); print("pptx saved")


if __name__ == "__main__":
    bump_docs()
    bump_pptx()
    print("done", NEWV)
