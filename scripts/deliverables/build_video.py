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

# Демо-сцены для шагов TOUR с полем shot (встроенный тур их не строит — он не меняет доску пользователя).
SCENES = {
 "board": """()=>{setPerm('editor');applyPerms();views();activate('board');
  ST.board.items=[];ST.board.session={};brdHistReset();const c=brdCam();c.x=0;c.y=0;c.z=1;brdInsertTemplate('ssc');
  const fr=brdItems().filter(x=>x.t==='frame'&&!/Ретро/.test(x.title||''));
  const add=(i,txt,col)=>{const f=fr[i];brdAdd({id:brdId(),t:'sticky',x:f.x+14,y:f.y+150,w:170,h:110,fill:col,text:txt,author:'Иванов',votes:2});};
  add(0,'Парное ревью для сложных задач','#A0E7A0');add(1,'Сдвигать дейли из-за встреч','#FF8A8A');add(2,'Демо каждую пятницу','#8FC7FF');
  const outer=brdItems().find(x=>x.t==='frame'&&/Ретро/.test(x.title));const bx=outer.x+outer.w+60,by=outer.y;
  (ST.tasks||[]).slice(0,3).forEach((t,i)=>brdAddTaskCard(t.id,bx,by+i*134));
  brdAdd({id:brdId(),t:'metric',m:'velocity',x:bx+250,y:by,w:230,h:120});
  brdAdd({id:brdId(),t:'metric',m:'risk',x:bx+250,y:by+134,w:230,h:120});
  brdAdd({id:brdId(),t:'metric',m:'goal',x:bx+250,y:by+268,w:230,h:120});BW.sel=[];}""",
 "board2": """()=>{setPerm('editor');applyPerms();views();activate('board');
  ST.board.items=[];ST.board.session={};brdHistReset();const c=brdCam();c.x=0;c.y=0;c.z=1;
  const F=(id,t,x,y,txt,w,h)=>brdAdd({id:id,t:t,x:x,y:y,w:w||170,h:h||70,fill:'#FFFFFF',stroke:'#2D5BE3',text:txt});
  F('f1','terminator',0,0,'Начало',170,60);F('f2','parallelogram',0,120,'Заявка клиента');F('f3','diamond',10,240,'Данные полные?',150,110);
  F('f4','rect',260,265,'Уточнить данные');F('f5','document',0,420,'Договор',170,90);F('f6','database',240,410,'CRM',130,100);F('f7','terminator',0,570,'Конец',170,60);
  const L=(a,b,l)=>brdAdd({id:brdId(),t:'conn',from:a,to:b,stroke:'#334155',label:l||undefined});
  L('f1','f2');L('f2','f3');L('f3','f5','да');L('f3','f4','нет');L('f5','f6','сохранить');L('f5','f7');
  brdAdd({id:'mr',t:'mind',x:960,y:230,w:190,h:56,text:'Релиз 2.0',mp:''});
  const k1=brdMindAdd('mr','child',true);k1.text='Оплата';const k2=brdMindAdd('mr','child',true);k2.text='Каталог';
  const k3=brdMindAdd(k1.id,'sibling',true);k3.text='Уведомления';const g1=brdMindAdd(k1.id,'child',true);g1.text='Apple Pay';
  const g2=brdMindAdd(g1.id,'sibling',true);g2.text='СБП';const g3=brdMindAdd(k2.id,'child',true);g3.text='Фильтры';brdMindLayout('mr');
  brdAdd({id:'tb',t:'table',x:620,y:540,w:480,h:120,rows:[['Риск','Владелец','Срок'],['Сбой оплаты','Иванов А.','Спринт 4'],['Задержка API','Петрова М.','Спринт 5']]});
  [['s1','Парное ревью',3],['s2','Демо по пятницам',5],['s3','Меньше встреч',2]].forEach((x,i)=>brdAdd({id:x[0],t:'sticky',x:620+i*190,y:-40,w:170,h:120,fill:'#FFE066',text:x[1],author:'Иванов',votes:x[2]}));
  ST.board.session={vote:{on:false,limit:3,hidden:true,revealed:true},anon:false};
  brdCmtAdd('f3','Согласовать критерии полноты с @'+ST.team[0].name);BW.sel=[];}""",
}
# Холст ниже плашки с подписью (нижние 300 px кадра): уменьшаем высоту, прокручиваем к холсту, вписываем.
FIT_BOARD = """()=>{const w=document.querySelector('#v_board .brd-wrap');if(!w)return;w.style.minHeight='0';
 window.scrollTo(0,w.getBoundingClientRect().top+window.scrollY-12);
 w.style.height=Math.max(420,innerHeight-300-14-w.getBoundingClientRect().top)+'px';
 const mm=document.getElementById('brd-mini');if(mm)mm.style.display='none';
 brdFit();const t=document.getElementById('toast');if(t)t.classList.remove('show');}"""

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
        tour = pg.evaluate("()=>TOUR.map(s=>({v:s.v,k:s.shot||s.v,h:s.h,p:s.p,d:s.d}))")
        for st in {s["k"]: s for s in tour}.values():
            pg.evaluate("(id)=>activate(id)", st["v"])
            pg.evaluate("()=>window.scrollTo(0,0)")
            if st["k"] in SCENES:   # демо-сцена только в браузере сборки — данные пользователя не трогаем
                pg.evaluate(SCENES[st["k"]]); pg.evaluate(FIT_BOARD); pg.wait_for_timeout(900)
            pg.wait_for_timeout(450)
            path = TMP / ("shot_" + st["k"] + ".png")
            pg.screenshot(path=str(path))
            shots[st["k"]] = path
        ctx.close(); b.close()
    print("captured", len(shots), "sections; TOUR steps:", len(tour))

    def compose(step, idx, total):
        base = Image.open(shots[step["k"]]).convert("RGB").resize((W, H))
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
