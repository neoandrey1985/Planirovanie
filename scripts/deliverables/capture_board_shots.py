# -*- coding: utf-8 -*-
"""Скриншоты «Доски» для презентации и документов (1440×810 @1.5 → 2160×1215, build/shots/*.jpg):
  board.jpg       — шаблон ретро, живые карточки задач и виджеты-метрики (выделение → панель действий);
  board_ergo.jpg  — эргономика: группа, закрепление, выравнивание, поиск, сетка, мини-карта;
  board_tpl.jpg   — меню шаблонов и шаблон «Кораблик» на холсте;
  board_sess.jpg  — сессия: итоги голосования с медалями, анонимный ввод, комментарий, панель «Сессия»;
  board2.jpg      — схемы: блок-схема с подписями, майнд-карта, таблица.
Сцены board/board2 берутся из build_video.SCENES — один источник для видео и слайдов.
Запуск: python scripts/deliverables/capture_board_shots.py [имя ...]"""
import sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_video import SCENES  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "shots"; OUT.mkdir(parents=True, exist_ok=True)
APP = (ROOT / "frontend" / "index.html").as_uri()
BASE = "()=>{setPerm('editor');applyPerms();views();activate('board');ST.board.items=[];ST.board.session={};brdHistReset();const c=brdCam();c.x=0;c.y=0;c.z=1;}"
SHOTS = {
 "board": [SCENES["board"], "()=>{brdFit();BW.sel=brdItems().filter(x=>x.t==='task').slice(0,2).map(x=>x.id);brdRender();}"],
 "board2": [SCENES["board2"], "()=>{brdFit();}"],
 "board_ergo": [BASE, """()=>{
   const S=(id,x,y,t,f)=>brdAdd({id:id,t:'sticky',x:x,y:y,w:160,h:120,fill:f,text:t,author:'Иванов',votes:0});
   brdAdd({id:'fz',t:'frame',x:-40,y:-60,w:1140,h:560,title:'Планирование спринта'});
   S('i1',0,0,'Идея: автотесты оплаты','#FFE066');S('i2',190,0,'Идея: кэш каталога','#FFE066');S('i3',380,0,'Идея: SSO','#FFE066');S('i4',570,0,'Идея: тёмная тема','#FFE066');
   brdAdd({id:'g1',t:'rect',x:40,y:230,w:170,h:80,fill:'#FFFFFF',stroke:'#2D5BE3',text:'API заказов',grp:'G1'});
   brdAdd({id:'g2',t:'database',x:300,y:220,w:140,h:100,fill:'#FFFFFF',stroke:'#2D5BE3',text:'БД',grp:'G1'});
   brdAdd({id:'gc',t:'conn',from:'g1',to:'g2',stroke:'#334155'});
   brdAdd({id:'lk',t:'sticky',x:820,y:20,w:200,h:150,fill:'#C6A0FF',text:'Цель спринта: оплата картой (закреплено)',author:'PO',votes:0,locked:true});
   brdAdd({id:'t1',t:'rect',x:560,y:240,w:170,h:70,fill:'#A0E7A0',stroke:'#2F9E44',text:'Выровнено'});
   brdAdd({id:'t2',t:'rect',x:760,y:240,w:170,h:70,fill:'#A0E7A0',stroke:'#2F9E44',text:'по верхнему краю'});
   BW.snap=true;views();activate('board');brdFit();
   const f=document.getElementById('brd-find');f.value='Идея';BW.findQ='Идея';brdFind('Идея');brdFindUI();
   BW.sel=['g1','g2'];brdRender();}"""],
 "board_tpl": [BASE, "()=>{brdInsertTemplate('sail');brdFit();const c=brdCam();c.x-=170;brdRender();brdToggleTplPanel();}"],
 "board_sess": [BASE, """()=>{brdInsertTemplate('ssc');const fr=brdItems().filter(x=>x.t==='frame'&&!/Ретро/.test(x.title||''));
   const add=(i,dy,txt,v)=>{const f=fr[i];brdAdd({id:'v'+i+dy,t:'sticky',x:f.x+14,y:f.y+150+dy,w:170,h:110,fill:['#A0E7A0','#FF8A8A','#8FC7FF'][i],text:txt,author:'Иванов',votes:v});};
   add(0,0,'Парное ревью сложных задач',5);add(1,0,'Длинные дейли',3);add(2,0,'Демо по пятницам',4);add(0,130,'Меньше встреч',1);
   ST.board.session={vote:{on:false,limit:3,hidden:true,revealed:true},anon:true,anonRevealed:false};
   brdCmtAdd('v10','Предлагаю попробовать со следующего спринта, @'+ST.team[0].name);
   brdFit();const c=brdCam();c.x-=170;brdRender();brdToggleSessPanel();}"""],
}
CLEAN = """()=>{const t=document.getElementById('toast');if(t)t.classList.remove('show');
 const w=document.querySelector('#v_board .brd-wrap');if(w)window.scrollTo(0,w.getBoundingClientRect().top+window.scrollY-70);brdMiniRender();}"""

want = sys.argv[1:] or list(SHOTS)
with sync_playwright() as p:
    b = p.chromium.launch()
    for name in want:
        ctx = b.new_context(viewport={"width": 1440, "height": 810}, device_scale_factor=1.5)
        pg = ctx.new_page(); pg.goto(APP)
        pg.wait_for_function("()=>typeof activate==='function'&&typeof ST!=='undefined'"); pg.wait_for_timeout(400)
        for js in SHOTS[name]: pg.evaluate(js)
        pg.wait_for_timeout(1900); pg.evaluate(CLEAN); pg.wait_for_timeout(300)
        raw = OUT / (name + "_raw.png"); pg.screenshot(path=str(raw))
        im = Image.open(raw).convert("RGB"); im = im.resize((2160, 1215)) if im.size != (2160, 1215) else im
        im.save(OUT / (name + ".jpg"), quality=88); raw.unlink(); ctx.close()
        print("captured", name + ".jpg")
    b.close()
