# -*- coding: utf-8 -*-
"""Rebuild the walkthrough video (Обзор_приложения.mp4) from the app's TOUR array.

Reusable across releases: steps, captions and durations come from the app's own
TOUR array, so new sections added to TOUR appear automatically. Captures each
referenced section at 1920x1080, composes a caption card, encodes to H.264 mp4.

Usage:
    python scripts/deliverables/build_video.py [out_mp4]

Default out_mp4 = <repo>/Обзор_приложения.mp4 . Requires: playwright, pillow,
imageio, imageio-ffmpeg, numpy.
"""
import sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
APP = (REPO / "frontend" / "index.html").as_uri()
DEST = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (REPO / "Обзор_приложения.mp4")
TMP = REPO / "build" / "vframes"
TMP.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1920, 1080, 10

FONT_DIR = pathlib.Path(r"C:/Windows/Fonts")
def font(name, size):
    for cand in (name, "segoeui.ttf", "arial.ttf"):
        p = FONT_DIR / cand
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()
F_TITLE, F_BODY, F_BADGE = font("segoeuib.ttf", 46), font("segoeui.ttf", 30), font("segoeuib.ttf", 24)


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    shots, tour = {}, []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg = ctx.new_page()
        pg.goto(APP)
        pg.wait_for_function("() => typeof activate === 'function' && typeof TOUR !== 'undefined'")
        pg.wait_for_timeout(400)
        tour = pg.evaluate("()=>TOUR.map(s=>({v:s.v,h:s.h,p:s.p,d:s.d}))")
        for v in dict.fromkeys(s["v"] for s in tour):
            pg.evaluate("(id)=>activate(id)", v)
            pg.evaluate("()=>window.scrollTo(0,0)")
            pg.wait_for_timeout(450)
            path = TMP / ("shot_" + v + ".png")
            pg.screenshot(path=str(path))
            shots[v] = path
        ctx.close(); b.close()
    print("captured", len(shots), "sections; TOUR steps:", len(tour))

    def compose(step, idx, total):
        base = Image.open(shots[step["v"]]).convert("RGB").resize((W, H))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        card_h = 300
        d.rectangle([0, H - card_h, W, H], fill=(14, 20, 28, 205))
        d.rectangle([0, H - card_h, 10, H], fill=(45, 91, 227, 255))
        img = Image.alpha_composite(base.convert("RGBA"), ov)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([W - 190, 28, W - 28, 74], radius=10, fill=(210, 69, 69, 255))
        d.text((W - 172, 36), "● ОБЗОР", font=F_BADGE, fill=(255, 255, 255))
        x, y = 46, H - card_h + 30
        d.text((x, y), step["h"], font=F_TITLE, fill=(255, 255, 255))
        y += 64
        for ln in wrap(d, step["p"], F_BODY, W - 90)[:4]:
            d.text((x, y), ln, font=F_BODY, fill=(205, 216, 230))
            y += 40
        d.rectangle([0, H - 6, W, H], fill=(38, 53, 71, 255))
        d.rectangle([0, H - 6, int(W * (idx + 1) / total), H], fill=(91, 132, 240, 255))
        return img.convert("RGB")

    writer = imageio.get_writer(str(DEST), fps=FPS, codec="libx264", quality=7,
                                macro_block_size=None, ffmpeg_params=["-pix_fmt", "yuv420p"])
    total = len(tour)
    for i, step in enumerate(tour):
        arr = np.asarray(compose(step, i, total))
        for _ in range(max(1, int(round(step.get("d", 7000) / 1000.0 * FPS)))):
            writer.append_data(arr)
    writer.close()
    print("saved", DEST, DEST.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
