# -*- coding: utf-8 -*-
"""Скриншот «Доски» для документации v1.49: блок-схема с подписями, майнд-карта, таблица, итоги голосования.
Пишет build/shots/board2.jpg (2160×1215). Запуск: python scripts/deliverables/capture_board_v149.py"""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "shots"; OUT.mkdir(parents=True, exist_ok=True)
APP = (ROOT / "frontend" / "index.html").as_uri()
SCENE = """()=>{setPerm('editor');applyPerms();views();activate('board');
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
 brdCmtAdd('f3','Согласовать критерии полноты с @'+ST.team[0].name);
 brdFit();BW.sel=[];brdRender();brdMiniRender();
 document.querySelectorAll('#toast').forEach(t=>t.classList.remove('show'));
 const w=document.querySelector('#v_board .brd-wrap');if(w)window.scrollTo(0,w.getBoundingClientRect().top+window.scrollY-70);}"""

with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1440, "height": 810}, device_scale_factor=1.5)
    pg = ctx.new_page(); pg.goto(APP)
    pg.wait_for_function("()=>typeof activate==='function'&&typeof ST!=='undefined'"); pg.wait_for_timeout(400)
    pg.evaluate(SCENE); pg.wait_for_timeout(2000)
    raw = OUT / "board2_raw.png"; pg.screenshot(path=str(raw))
    im = Image.open(raw).convert("RGB"); im = im.resize((2160, 1215)) if im.size != (2160, 1215) else im
    im.save(OUT / "board2.jpg", quality=88); raw.unlink(); ctx.close(); b.close()
print("captured board2.jpg")
