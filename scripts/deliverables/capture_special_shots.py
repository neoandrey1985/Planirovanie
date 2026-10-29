# -*- coding: utf-8 -*-
"""Специальные кадры для документов и презентации (1440×810 @1.5 → 2160×1215, build/shots/<имя>.jpg):
дашборд в режиме администратора, окно входа, помощник, фрагменты разделов (распределения в аналитике, диаграмма Исикавы, форматы ретро),
релизная доска и «Состав релизов» на Kanban, окно отчёта по спринту, окна администратора (на подменённых
ответах сервера) кадры эргономики v1.50 («Мой день», вкладки хаба, меню, первые шаги, мастер) и «Мой профиль» v1.51.
Разделы целиком — capture_shots.py, доска — capture_board_shots.py.
Запуск: python scripts/deliverables/capture_special_shots.py [имя ...]"""
import sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "shots"; OUT.mkdir(parents=True, exist_ok=True)
APP = (ROOT / "frontend" / "index.html").as_uri()


def scroll_to_text(view, text, dy=-80):
    """Активировать раздел и прокрутить к самому вложенному элементу с данным текстом."""
    return ("()=>{activate(%r);const all=[...document.querySelectorAll('#v_%s *')].filter(e=>e.children.length<3&&e.textContent.includes(%r));"
            "const e=all[all.length-1]||null;if(e){e.scrollIntoView({block:'start'});window.scrollBy(0,%d);}else window.scrollTo(0,0);}") % (view, view, text, dy)


ADMIN = "()=>{setPerm('admin');applyPerms();updateRoleBtn();}"
SHOTS = {
 "usermgmt": [ADMIN, "()=>{activate('dash');window.scrollTo(0,0);}"],
 "login": ["()=>{activate('dash');window.scrollTo(0,0);openLogin();}"],
 "chat": ["()=>{activate('dash');window.scrollTo(0,0);document.getElementById('chatfab').click();}"],
 "analytics_dist": [scroll_to_text("analytics", "Распределение объёма по типам")],
 "risks_ishikawa": [scroll_to_text("risks", "Диаграмма Исикавы", -60)],
 "retro_mood": [scroll_to_text("retro", "Форматы ретроспектив", -260)],
 "kanban_release": ["()=>{UI.kanBoard='b-release';views();activate('kanban');window.scrollTo(0,0);}"],
 "kanban_compose": ["()=>{UI.kanBoard='b-release-compose';views();activate('kanban');window.scrollTo(0,0);}"],
 "report": ["()=>{activate('dash');window.scrollTo(0,0);const C=compute();const n=(typeof doneSprintForReport==='function'&&doneSprintForReport(C))||C.cur;openPptxModalFor(n);}"],
 # эргономика v1.50: «Мой день», вкладки хаба и компактное меню, меню «＋ Создать» и пользователя, первые шаги, мастер
 "s_myday": [ADMIN, "()=>{lsSetS('me',ST.team[0].name);views();activate('myday');window.scrollTo(0,0);}"],
 "s_hubs": [ADMIN, "()=>{activate('wsjf');window.scrollTo(0,0);}"],
 "s_menus": [ADMIN, "()=>{activate('dash');window.scrollTo(0,0);}", "()=>{document.getElementById('qcbtn').click();}"],
 "s_umenu": [ADMIN, "()=>{activate('dash');window.scrollTo(0,0);}", "()=>{document.getElementById('ubtn').click();}"],
 "s_onb": [ADMIN, "()=>{const st=blankState(ST);st.params.name='Мобильное приложение';st.team=[{name:'Орлова Е.',role:'Frontend',avail:1,absent:0}];"
                  "ST=migrate(st);save();views();activate('dash');window.scrollTo(0,0);}"],
 "s_wizard": [ADMIN, "()=>{activate('dash');window.scrollTo(0,0);projOpen();const m=document.getElementById('projmodal');"
                     "m.querySelector('[data-w=name]').value='Мобильное приложение';m.querySelector('[data-w=goal]').value='Выпустить MVP к весне';"
                     "m.querySelector('[data-w=team]').value=['Орлова Е. — Frontend','Белов И. — QA','Новиков П. — Backend'].join(String.fromCharCode(10));"
                     "m.querySelector('[data-w=tasks]').value=['Прототип главного экрана','Авторизация по телефону','Каталог товаров'].join(String.fromCharCode(10));}"],
 # «Мой профиль» (v1.51): серверный сеанс на подменённых ответах — видны логин, привязка и смена пароля
 "s_profile": ["MOCK", "()=>{AUTH.username='ivanov';AUTH.user='Иванов Алексей';AUTH.role='EDITOR';AUTH.member='Иванов А.';setPerm('editor');applyPerms();updateRoleBtn();"
               "ST.board.items=ST.board.items||[];ST.board.items.push({id:'pf1',t:'sticky',x:0,y:0,w:100,h:80,text:'Ретро',comments:[{id:'c1',a:'Петрова М.',"
               "t:'@Иванов А. проверь, пожалуйста, вебхуки оплаты',ts:'2026-09-09T10:00:00Z',m:['Иванов А.']}]});views();activate('profile');window.scrollTo(0,0);}"],
 "s_profile2": ["MOCK", "()=>{AUTH.username='ivanov';AUTH.user='Иванов Алексей';AUTH.role='EDITOR';AUTH.member='Иванов А.';setPerm('editor');applyPerms();updateRoleBtn();"
                "views();activate('profile');const c=[...document.querySelectorAll('#prof_root .md-h')].find(x=>x.textContent==='Настройки');if(c){c.scrollIntoView({block:'start'});window.scrollBy(0,-120);}}"],
 # «Гант по иерархии»: уровень «до историй», вид на сетку
 "s_hgantt": ["()=>{HG.level=3;HG.open={};HG.fact=true;views();activate('hgantt');const g=document.querySelector('#hg_root .hg-bar');if(g){g.scrollIntoView({block:'start'});window.scrollBy(0,-70);}}"],
 "s_stages": ["()=>{setPerm('editor');applyPerms();updateRoleBtn();HG.level=3;HG.open={};HG.fact=true;HG.marks=true;views();activate('hgantt');const g=document.querySelector('#hg_root .hg-grid');if(g){g.scrollIntoView({block:'start'});window.scrollBy(0,-60);}}"],
 "s_stlegend": ["()=>{setPerm('editor');applyPerms();updateRoleBtn();HG.level=2;HG.open={};HG.marks=true;views();activate('hgantt');const g=document.querySelector('#hg_root .hg-mleg');if(g){g.scrollIntoView({block:'end'});window.scrollBy(0,40);}}"],
 "s_stpanel": ["()=>{setPerm('editor');applyPerms();updateRoleBtn();HG.level=3;HG.open={};HG.marks=true;views();activate('hgantt');window.scrollTo(0,0);hgStagesOpen('FE-1');}"],
 "s_links": ["()=>{setPerm('editor');applyPerms();updateRoleBtn();HG.level=9;HG.open={};HG.marks=false;HG.links=true;views();activate('hgantt');}", "async()=>{await new Promise(r=>setTimeout(r,500));hgRefresh();await new Promise(r=>setTimeout(r,100));const g=document.querySelector('#hg_root .hg-grid');if(g){g.scrollIntoView({block:'start'});window.scrollBy(0,-60);}hgDrawLinks();}"],
 "s_links2": ["()=>{setPerm('editor');applyPerms();updateRoleBtn();HG.level=2;HG.open={};HG.marks=false;HG.links=true;views();activate('hgantt');}", "async()=>{await new Promise(r=>setTimeout(r,500));hgRefresh();await new Promise(r=>setTimeout(r,100));const g=document.querySelector('#hg_root .hg-grid');if(g){g.scrollIntoView({block:'start'});window.scrollBy(0,-60);}hgDrawLinks();}"],
 "s_linkpanel": ["()=>{setPerm('editor');applyPerms();updateRoleBtn();HG.level=3;HG.open={};HG.marks=true;views();activate('hgantt');window.scrollTo(0,0);hgStagesOpen('T-14');}"],
 # серверные окна администратора — на подменённых ответах сервера (демо-учётки, без реальных данных)
 "admin_users": ["MOCK", "async()=>{activate('dash');window.scrollTo(0,0);await openUsers();}"],
 "admin_audit": ["MOCK", "async()=>{views();activate('audit');await new Promise(r=>setTimeout(r,600));"
                 "const t=[...document.querySelectorAll('#v_audit .ctitle')].pop();if(t){t.scrollIntoView({block:'start'});window.scrollBy(0,-90);}}"],
}
MOCK = r"""()=>{AUTH.mode='server';AUTH.token='demo';AUTH.username='admin';AUTH.user='Администратор';AUTH.role='ADMIN';setPerm('admin');applyPerms();updateRoleBtn();
 const U=[{username:'admin',name:'Администратор',role:'ADMIN',active:true},{username:'po',name:'Петрова М. (Product Owner)',role:'EDITOR',active:true},
  {username:'dev.back',name:'Иванов А.',role:'EDITOR',active:true},{username:'qa',name:'Соколов Р.',role:'EDITOR',active:true},{username:'viewer',name:'Наблюдатель',role:'VIEWER',active:true}];
 const now=Date.parse('2026-09-10T10:42:00Z'),E=[['AUTH','login','po','POST','/api/auth/login',200,'Вход выполнен'],
  ['DATA','state_saved','po','PUT','/api/state',200,'Сохранение данных, версия 57'],['CLIENT','quick_create','po','UI','',null,'task:T-21'],
  ['ACCESS','PUT','dev.back','PUT','/api/state',200,null],['ACCESS','POST','admin','POST','/api/auth/users',200,null],
  ['DENY','PUT','viewer','PUT','/api/state',403,null],['DATA','state_saved','qa','PUT','/api/state',200,'Сохранение данных, версия 58'],
  ['CLIENT','export_xlsx','po','UI','',null,'Планирование_спринта_PRO.xlsx']]
  .map((e,i)=>({ts:now-i*137000,category:e[0],action:e[1],username:e[2],method:e[3],path:e[4],status:e[5],detail:e[6]}));
 const orig=window.fetch;window.fetch=(u,o)=>{const s=String(u);const J=x=>Promise.resolve(new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}}));
  if(s.includes('api/auth/users'))return J(U);if(s.includes('api/audit'))return J({enabled:true,total:E.length,events:E});return orig(u,o);};}"""

want = sys.argv[1:] or list(SHOTS)
with sync_playwright() as p:
    b = p.chromium.launch()
    for name in want:
        ctx = b.new_context(viewport={"width": 1440, "height": 810}, device_scale_factor=1.5)
        pg = ctx.new_page(); pg.goto(APP)
        pg.wait_for_function("()=>typeof activate==='function'&&typeof NAV!=='undefined'"); pg.wait_for_timeout(400)
        for js in SHOTS[name]: pg.evaluate(MOCK if js == "MOCK" else js)
        pg.wait_for_timeout(1000)
        pg.evaluate("()=>{const t=document.getElementById('toast');if(t)t.classList.remove('show');}")
        raw = OUT / (name + "_raw.png"); pg.screenshot(path=str(raw))
        im = Image.open(raw).convert("RGB"); im = im.resize((2160, 1215)) if im.size != (2160, 1215) else im
        im.save(OUT / (name + ".jpg"), quality=88)
        for _ in range(20):
            try: raw.unlink(); break
            except PermissionError: pg.wait_for_timeout(250)
        ctx.close(); print("captured", name + ".jpg")
    b.close()
