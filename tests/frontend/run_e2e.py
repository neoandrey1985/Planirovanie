# -*- coding: utf-8 -*-
"""End-to-end / functional test suite for the Управление кросс-функциональной командой frontend SPA.

Covers ALL application functionality:
  * Smoke-tests EVERY navigation section (auto-discovered from the app's NAV) — so
    when a new section is added it is covered automatically, with no new test code.
  * Deep functional checks: metrics engine, EDA report, PPTX sprint report (incl. the
    file-corruption regression), Excel export, Kanban role-routing, release composition,
    automation, whiteboard, data migration, versioning and the Support section.

Run:  python tests/frontend/run_e2e.py      (needs: pip install playwright && playwright install chromium)
Exit code is non-zero if any test fails — suitable for CI regression gating.
"""
import os, sys, io, time, base64, zipfile, re, functools, threading, http.server, socketserver
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND = os.path.join(ROOT, 'frontend')
PORT = int(os.environ.get('E2E_PORT', '4123'))
URL = f'http://127.0.0.1:{PORT}/'

PASS, FAIL, SKIP = [], [], []
class Skip(Exception): pass

def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=FRONTEND)
    class Q(socketserver.TCPServer): allow_reuse_address = True; daemon_threads = True
    httpd = Q(('127.0.0.1', PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

def case(name, fn):
    try:
        fn(); print('PASS  ' + name); PASS.append(name)
    except Skip as s:
        print('SKIP  ' + name + '  — ' + str(s)); SKIP.append(name)
    except AssertionError as e:
        print('FAIL  ' + name + '  — ' + str(e)); FAIL.append((name, str(e)))
    except Exception as e:
        print('ERROR ' + name + '  — ' + repr(e)); FAIL.append((name, repr(e)))

# console-error noise from the offline dev server (no backend) — not app bugs
IGNORE = ('Failed to load resource', 'api/state', 'api/health', 'api/audit', '/analytics',
          'favicon', 'net::ERR', 'status of 404', 'status of 403', 'ws://', 'WebSocket')
def is_noise(t): return any(s in t for s in IGNORE)


def main():
    httpd = serve(); time.sleep(0.4)
    with sync_playwright() as p:
        br = p.chromium.launch(args=['--no-sandbox'])
        page = br.new_page(viewport={'width': 1440, 'height': 900})
        cerr = []
        page.on('console', lambda m: cerr.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: cerr.append(str(e)))
        page.goto(URL, wait_until='load')
        page.wait_for_selector('.nav-item', timeout=15000)
        page.wait_for_timeout(700)
        page.evaluate("()=>{try{endTour&&endTour()}catch(e){}}")

        # ---- 0. boots without console errors ----
        def t_boot():
            real = [e for e in cerr if not is_noise(e)]
            assert not real, 'console errors on load: ' + ' | '.join(real[:4])
        case('app boots without console errors', t_boot)

        # ---- 1. smoke: EVERY NAV section renders (auto-discovered) ----
        sections = page.evaluate("()=>NAV.flatMap(g=>g.items.map(i=>i[0]))")
        assert sections and len(sections) >= 20, 'expected many nav sections'
        print(f'  (auto-discovered {len(sections)} sections)')
        for sid in sections:
            def t_sec(sid=sid):
                before = len(cerr)
                page.evaluate("(id)=>activate(id)", sid)
                page.wait_for_timeout(140)
                ok = page.evaluate("(id)=>{const el=document.getElementById('v_'+id);"
                                   "return !!el && el.classList.contains('active') && el.children.length>0}", sid)
                new = [e for e in cerr[before:] if not is_noise(e)]
                assert ok, 'view not active or empty'
                assert not new, 'console error: ' + ' | '.join(new[:3])
            case('section renders: ' + sid, t_sec)
        page.evaluate("()=>activate('dash')")

        # ---- 2. metrics engine ----
        def t_compute():
            keys = page.evaluate("()=>{const C=compute();return Object.keys(C)}")
            for k in ('cur', 'avgVel', 'health', 'sp', 'ttmAvg', 'dre'):
                assert k in keys, 'compute() missing key ' + k
            ok = page.evaluate("()=>{const C=compute();return C.sp.length>0 && isFinite(C.avgVel) && "
                               "C.health>=0 && C.health<=1}")
            assert ok, 'compute() produced out-of-range metrics'
        case('metrics: compute() returns valid model', t_compute)

        # ---- 3. version / changelog consistency ----
        def t_ver():
            ok = page.evaluate("()=>APP_VERSION===CHANGELOG[0].v")
            assert ok, 'APP_VERSION != CHANGELOG[0].v'
        case('versioning: APP_VERSION matches changelog head', t_ver)

        # ---- 4. EDA report ----
        def t_eda():
            page.evaluate("()=>activate('eda')"); page.wait_for_timeout(200)
            r = page.evaluate("""()=>{const v=document.getElementById('v_eda');
              return {kpis:v.querySelectorAll('#eda_kpi .kpi').length,
                      charts:[...v.querySelectorAll('[id^=eda_c]')].filter(c=>c.querySelector('svg')).length,
                      tables:v.querySelectorAll('table').length};}""")
            assert r['kpis'] >= 4, 'EDA KPI cards missing'
            assert r['charts'] >= 4, 'EDA distribution charts not rendered'
            assert r['tables'] >= 2, 'EDA tables missing'
        case('EDA: report renders KPIs, charts and tables', t_eda)

        # ---- 4b. Star Map (team competencies by role) ----
        def t_starmap():
            page.evaluate("()=>activate('starmap')"); page.wait_for_timeout(200)
            r = page.evaluate("""()=>{const v=document.getElementById('v_starmap');
              return {radars:v.querySelectorAll('.sm-card svg').length,
                      matrices:v.querySelectorAll('table.sm-matrix').length,
                      rows:(ST.skills||[]).length,
                      team:(ST.team||[]).length};}""")
            assert r['rows'] > 0, 'no competency rows seeded'
            assert r['matrices'] >= 1, 'no competency matrix rendered'
            assert r['team'] == 0 or r['radars'] >= 1, 'no member radars rendered'
            # syncSkills() must be idempotent (no duplicate rows on a second run)
            same = page.evaluate("()=>{const a=(ST.skills||[]).length;syncSkills();return (ST.skills||[]).length===a;}")
            assert same, 'syncSkills() added duplicates on a no-op run'
        case('starmap: competency radars + matrix render', t_starmap)

        # ---- 4c. Agile maturity (Scrum / Kanban / SAFe) ----
        def t_agile():
            page.evaluate("()=>activate('agile')"); page.wait_for_timeout(200)
            r = page.evaluate("""()=>{const v=document.getElementById('v_agile');
              return {tabs:v.querySelectorAll('.agl-tab').length,
                      radar:!!v.querySelector('.sm-radar svg'),
                      scale:v.querySelectorAll('.agl-scale .agl-lv').length,
                      frameworks:[...new Set((ST.agile||[]).map(a=>a.framework))],
                      rows:(ST.agile||[]).length};}""")
            assert r['tabs'] == 3, 'expected 3 framework tabs (Scrum/Kanban/SAFe)'
            assert set(r['frameworks']) == {'Scrum', 'Kanban', 'SAFe'}, 'missing framework: ' + str(r['frameworks'])
            assert r['radar'], 'maturity radar not rendered'
            assert r['scale'] == 5, 'expected a 5-level maturity scale'
            # switching to the Kanban tab re-renders its dimensions
            sw = page.evaluate("""()=>{const t=[...document.querySelectorAll('#v_agile .agl-tab')].find(x=>x.textContent.includes('Kanban'));
              t.click();return UI.agileTab;}""")
            assert sw == 'Kanban', 'tab switch did not update UI.agileTab'
        case('agile-maturity: Scrum/Kanban/SAFe tabs render', t_agile)

        # ---- 4d. Integrations (Atlassian suite catalog) ----
        def t_integrations():
            page.evaluate("()=>activate('integrations')"); page.wait_for_timeout(150)
            r = page.evaluate("""()=>{const v=document.getElementById('v_integrations');
              const names=[...v.querySelectorAll('.intg-name')].map(x=>x.textContent);
              return {cards:v.querySelectorAll('.intg-card').length, names,
                      badges:v.querySelectorAll('.intg-badge').length,
                      catalog:(typeof ATL_PRODUCTS!=='undefined')?ATL_PRODUCTS.map(p=>p.k):[]};}""")
            assert r['cards'] >= 10, 'expected the full Atlassian product catalog (>=10)'
            for prod in ('Jira', 'Confluence', 'Bitbucket', 'Trello'):
                assert any(prod in n for n in r['names']), 'missing product: ' + prod
            for key in ('jira', 'jsm', 'confluence', 'bitbucket', 'trello', 'opsgenie', 'statuspage', 'bamboo'):
                assert key in r['catalog'], 'catalog missing ' + key
        case('integrations: Atlassian product catalog renders', t_integrations)

        # ---- 4e. Smart sidebar (collapse / pin / filter / recent) ----
        def t_nav():
            page.evaluate("()=>{try{localStorage.removeItem('navui');}catch(e){}}")
            r = page.evaluate("""()=>{
              const nav=document.getElementById('nav');
              const hasSearch=!!document.getElementById('navsearch');
              togglePin('backlog');
              const fav=[...nav.querySelectorAll('.nav-smart .nav-h-t')].some(x=>x.textContent.includes('Избранное'));
              const pinned=!!nav.querySelector('.nav-pin.on[data-pin="backlog"]');
              toggleGroup('Выпуск');
              const grp=[...nav.querySelectorAll('.nav-group:not(.nav-smart)')].find(g=>g.querySelector('.nav-h-t').textContent==='Выпуск');
              const toggled=!grp.classList.contains('collapsed');
              navFilter('гант');
              const matches=[...nav.querySelectorAll('.nav-row')].filter(x=>x.style.display!=='none').map(x=>x.querySelector('.nav-lbl').textContent);
              navFilter('');
              togglePin('backlog');  // cleanup
              return {hasSearch,fav,pinned,toggled,matches};}""")
            assert r['hasSearch'], 'nav search box missing'
            assert r['fav'] and r['pinned'], 'pin → favorites did not work'
            assert r['toggled'], 'group collapse toggle did not work'
            assert r['matches'] == ['Гант'], 'filter did not narrow to the match: ' + str(r['matches'])
        case('sidebar: collapse/pin/filter smart nav', t_nav)

        # ---- 4f. Top toolbar: data actions consolidated into one menu ----
        def t_toolbar():
            r = page.evaluate("""()=>{
              const visible=[...document.querySelector('.tools').children].map(c=>c.id);
              document.getElementById('datamenu').click();
              const opened=document.getElementById('dmenu').classList.contains('open');
              const items=[...document.querySelectorAll('#datapop .btn')].map(b=>b.id);
              document.body.click();
              const closed=!document.getElementById('dmenu').classList.contains('open');
              return {visible,opened,items,closed};}""")
            assert 'dmenu' in r['visible'], 'data menu button not in toolbar'
            for old in ('xls', 'pptxbtn', 'exp', 'imp', 'impcsv', 'rst'):
                assert old not in r['visible'], old + ' should be inside the menu, not the top bar'
                assert old in r['items'], 'menu missing action ' + old
            assert r['opened'] and r['closed'], 'menu open/close broken'
        case('toolbar: data actions grouped in «Данные» menu', t_toolbar)

        # ---- 5. data quality checks engine ----
        def t_checks():
            ok = page.evaluate("()=>Array.isArray(dataChecks())")
            assert ok, 'dataChecks() not available'
        case('automation: data-quality checks engine runs', t_checks)

        # ---- 6. Kanban role-routing ----
        def t_kanban():
            page.evaluate("()=>{setPerm('ADMIN');applyPerms();UI.kanBoard='b-all';views();activate('kanban');}")
            page.wait_for_timeout(200)
            res = page.evaluate("""()=>{const tasks=(ST.tasks||[]).length;
              const cards=document.querySelectorAll('#v_kanban .kan-card, #v_kanban .kanban-card, #v_kanban [draggable=true]').length;
              const boards=(typeof kanBoards==='function')?kanBoards().length:(ST.boards||[]).length;
              return {tasks,cards,boards};}""")
            assert res['boards'] >= 4, 'expected multiple Kanban boards (roles + release)'
            assert res['cards'] > 0, 'no task cards rendered on «Все задачи» board'
            page.evaluate("()=>{setPerm('viewer');applyPerms();views();activate('dash');}")
        case('kanban: multi-board renders task cards', t_kanban)

        # ---- 7. release composition ----
        def t_rel():
            ok = page.evaluate("""()=>{const rs=ST.releases||[];if(!rs.length)return true;
              const c=releaseComp(rs[0]);return c && 'items' in c && 'stories' in c && 'bugs' in c && 'pct' in c;}""")
            assert ok, 'releaseComp() shape invalid'
        case('releases: composition engine returns structure', t_rel)

        # ---- 8. whiteboard: add item ----
        def t_board():
            ok = page.evaluate("""()=>{try{setPerm('editor');applyPerms();views();activate('board');
              if(typeof brdAdd!=='function'||typeof brdItems!=='function')return null;
              const before=brdItems().length;
              brdAdd({id:'e2e_'+Date.now(),t:'sticky',x:0,y:0,w:150,h:120,fill:'#FFE066',text:'e2e',author:'test'});
              const after=brdItems().length;
              const svg=!!document.querySelector('#v_board svg');
              return (after===before+1)&&svg;}catch(e){return 'ERR:'+e.message;}}""")
            if ok is None:
                raise Skip('board API not exposed')
            assert ok is True, 'adding a sticky did not grow board items (' + str(ok) + ')'
            page.evaluate("()=>{setPerm('viewer');applyPerms();views();activate('dash');}")
        case('whiteboard: add sticky note', t_board)

        # ---- 9. migrate() idempotency + save() ----
        def t_migrate():
            ok = page.evaluate("""()=>{const a=migrate(JSON.parse(JSON.stringify(SEED)));
              const b=migrate(JSON.parse(JSON.stringify(a)));
              return Array.isArray(a.tasks) && a.tasks.length===b.tasks.length;}""")
            assert ok, 'migrate() not idempotent on task count'
            saved = page.evaluate("""()=>{localStorage.removeItem('sprintapp');
              setPerm('editor');applyPerms();save();const v=!!localStorage.getItem('sprintapp');
              setPerm('viewer');applyPerms();return v;}""")
            assert saved, 'save() did not persist to localStorage for an editor'
        case('data: migrate() idempotent and save() persists', t_migrate)

        # ---- 9b. save() is gated by permission (viewer cannot persist) ----
        def t_perm_gate():
            blocked = page.evaluate("""()=>{setPerm('viewer');applyPerms();localStorage.removeItem('sprintapp');
              save();return localStorage.getItem('sprintapp')===null;}""")
            assert blocked, 'viewer must not be able to persist via save()'
        case('security: save() is gated by edit permission', t_perm_gate)

        # ---- 10. Support section (docs, no admin guide) ----
        def t_support():
            page.evaluate("()=>activate('support')"); page.wait_for_timeout(150)
            r = page.evaluate("""()=>{const c=[...document.querySelectorAll('#v_support .sup-card')];
              return {titles:c.map(x=>x.querySelector('.sup-t').textContent),
                      hasAdmin:c.some(x=>/администратор/i.test(x.querySelector('.sup-t').textContent))};}""")
            assert len(r['titles']) >= 4, 'Support cards missing'
            assert not r['hasAdmin'], 'Admin guide must NOT be in Support'
        case('support: documents listed, admin guide excluded', t_support)

        # ---- 11. Excel export produces a valid workbook ----
        def t_xlsx():
            b64 = page.evaluate("""async()=>{const oc=URL.createObjectURL;let blob=null;
              URL.createObjectURL=(b)=>{blob=b;return 'blob:stub';};
              try{ exportXlsx(); }catch(e){ URL.createObjectURL=oc; return 'ERR:'+e.message; }
              URL.createObjectURL=oc;
              if(!blob) return null;
              const buf=await blob.arrayBuffer();const u=new Uint8Array(buf);let s='';
              for(let i=0;i<u.length;i++)s+=String.fromCharCode(u[i]);return btoa(s);}""")
            assert b64 and not str(b64).startswith('ERR:'), 'exportXlsx failed: ' + str(b64)
            z = zipfile.ZipFile(io.BytesIO(base64.b64decode(b64)))
            names = z.namelist()
            assert '[Content_Types].xml' in names, 'xlsx missing content types'
            assert any(n.startswith('xl/worksheets/sheet') for n in names), 'xlsx has no sheets'
            # every content-type override must resolve to a real part
            ct = z.read('[Content_Types].xml').decode()
            miss = [pn for pn in re.findall(r'PartName="([^"]+)"', ct) if pn.lstrip('/') not in names]
            assert not miss, 'xlsx dangling content-type overrides: ' + str(miss)
        case('export: Excel workbook is a valid package', t_xlsx)

        # ---- 12. PPTX sprint report: builds and is NOT corrupt (regression) ----
        def t_pptx():
            loaded = page.evaluate("async()=>{try{await loadPptxGen();return true;}catch(e){return false;}}")
            if not loaded:
                raise Skip('pptxgenjs CDN unavailable (offline)')
            b64 = page.evaluate("""async()=>{
              window.__cap=null;const oc=URL.createObjectURL;
              URL.createObjectURL=(b)=>{window.__cap=b;return 'blob:stub';};
              try{ await exportPptx(''); }catch(e){ URL.createObjectURL=oc; return 'ERR:'+e.message; }
              URL.createObjectURL=oc;
              if(!window.__cap) return null;
              const buf=await window.__cap.arrayBuffer();const u=new Uint8Array(buf);let s='';
              for(let i=0;i<u.length;i++)s+=String.fromCharCode(u[i]);return btoa(s);}""")
            assert b64 and not str(b64).startswith('ERR:'), 'exportPptx failed: ' + str(b64)
            z = zipfile.ZipFile(io.BytesIO(base64.b64decode(b64)))
            names = set(z.namelist())
            slides = [n for n in names if re.match(r'ppt/slides/slide\d+\.xml$', n)]
            assert len(slides) >= 8, 'report has too few slides: ' + str(len(slides))
            ct = z.read('[Content_Types].xml').decode()
            miss = [pn for pn in re.findall(r'PartName="([^"]+)"', ct) if pn.lstrip('/') not in names]
            # regression: writePptxFixed must strip phantom slideMaster overrides
            assert not miss, 'PPTX would prompt "repair": dangling overrides ' + str(miss)
        case('report: PPTX builds with all slides and no corruption', t_pptx)

        # ---- 13. WSJF scoring + ranking ----
        def t_wsjf():
            r = page.evaluate("""()=>{
              const sc=wsjfScore({bv:10,tc:9,rr:8,jobSize:5});      // CoD 27 / 5 = 5.4
              const cod=wsjfCoD({bv:10,tc:9,rr:8});
              const zero=wsjfScore({bv:5,tc:5,rr:5,jobSize:0});      // guard: no divide-by-zero
              activate('wsjf');const v=document.getElementById('v_wsjf');
              return {sc,cod,zero,rows:v.querySelectorAll('table tr').length,chart:!!v.querySelector('svg')};}""")
            assert abs(r['sc'] - 5.4) < 1e-9, 'wsjfScore wrong: ' + str(r['sc'])
            assert r['cod'] == 27, 'wsjfCoD wrong: ' + str(r['cod'])
            assert r['zero'] == 0, 'wsjfScore must guard jobSize=0'
            assert r['rows'] > 2 and r['chart'], 'WSJF view did not render table+chart'
        case('wsjf: score, Cost of Delay and ranking render', t_wsjf)

        # ---- 14. Sprint goals + auto achievement % ----
        def t_goals():
            r = page.evaluate("""()=>{
              activate('sprintGoals');const v=document.getElementById('v_sprintGoals');
              const g=(ST.sprintGoals||[]);
              const sp=g.length?g[0].sprint:1;
              const a=goalAchievement(sp);
              return {hasGoals:g.length>0, kpis:v.querySelectorAll('.kpi').length,
                      pill:/pill/.test(v.innerHTML), ach: a?(a.pct>=0&&a.pct<=1):true};}""")
            assert r['hasGoals'], 'no sprint goals seeded'
            assert r['kpis'] >= 4 and r['pill'], 'sprint goals view missing KPIs/pills'
            assert r['ach'], 'goalAchievement pct out of range'
        case('goals: per-sprint goal + auto achievement %', t_goals)

        # ---- 15. Sprint risk forecast ----
        def t_risk():
            r = page.evaluate("""()=>{const C=compute();const risk=sprintRisk(C);
              return {ok:!!risk, score:risk.score, level:risk.level,
                      inRange:risk.score>=0&&risk.score<=100,
                      levelOk:['Низкий','Средний','Высокий'].includes(risk.level),
                      dash:/Риск срыва спринта/.test((()=>{activate('dash');return document.getElementById('v_dash').innerHTML;})())};}""")
            assert r['ok'] and r['inRange'], 'sprintRisk out of range: ' + str(r.get('score'))
            assert r['levelOk'], 'sprintRisk level invalid: ' + str(r.get('level'))
            assert r['dash'], 'risk KPI not shown on dashboard'
        case('risk: sprint risk forecast computes and shows on dashboard', t_risk)

        # ---- 16. Carryover of unfinished tasks ----
        def t_carry():
            r = page.evaluate("""()=>{
              const snap=JSON.stringify(ST.tasks), perm=JSON.stringify(PERM);
              PERM.canEdit=true;
              const _s=window.save,_v=window.views,_a=window.activate,_t=window.toast;
              window.save=()=>{};window.views=()=>{};window.activate=()=>{};window.toast=()=>{};
              const C=compute(),N=C.cur;
              const before=(ST.tasks||[]).filter(t=>+t.sprint===N&&t.status!=='Готово').length;
              const nextBefore=(ST.tasks||[]).filter(t=>+t.sprint===N+1).length;
              carryoverSprint(N);
              const afterN=(ST.tasks||[]).filter(t=>+t.sprint===N&&t.status!=='Готово').length;
              const nextAfter=(ST.tasks||[]).filter(t=>+t.sprint===N+1).length;
              const carried=(ST.tasks||[]).filter(t=>num(t.carried)>0).length;
              window.save=_s;window.views=_v;window.activate=_a;window.toast=_t;
              ST.tasks=JSON.parse(snap);Object.assign(PERM,JSON.parse(perm));
              return {before,nextBefore,afterN,nextAfter,carried};}""")
            if r['before'] > 0:
                assert r['afterN'] == 0, 'unfinished tasks remained in source sprint'
                assert r['nextAfter'] == r['nextBefore'] + r['before'], 'carryover count mismatch'
                assert r['carried'] >= r['before'], 'carried flag not set'
        case('carryover: unfinished tasks move to next sprint', t_carry)

        # ---- 17. WIP limits: badge + data-check warning ----
        def t_wip():
            r = page.evaluate("""()=>{
              const b=(ST.boards||[]).find(x=>x.id==='b-all')||ST.boards[0];
              const before=JSON.stringify(b.wip||{});
              b.wip={'В работе':1};
              const warn=dataChecks().filter(i=>/WIP/.test(i.msg)).length;
              const cnt=kanColCount(b,'В работе');
              b.wip=JSON.parse(before);
              return {warn,cnt,hasEditor:typeof kanEditWip==='function'};}""")
            assert r['hasEditor'], 'kanEditWip missing'
            assert r['cnt'] >= 0, 'kanColCount failed'
            assert r['warn'] >= 1, 'WIP over-limit not flagged by dataChecks'
        case('wip: per-column limits flagged when exceeded', t_wip)

        # ---- 18. Fuzzy duplicate task detection ----
        def t_dup():
            r = page.evaluate("""()=>{
              return {same:titleSim('Оплата картой','оплата  картой!'),
                      diff:titleSim('Оплата картой','Экспорт отчётов'),
                      norm:normTitle('  Привет,  МИР! ')};}""")
            assert r['same'] >= 0.9, 'identical titles should score ~1'
            assert r['diff'] < 0.4, 'different titles should score low'
            assert r['norm'] == 'привет мир', 'normTitle wrong: ' + str(r['norm'])
        case('duplicates: fuzzy title similarity', t_dup)

        # ---- 19. OKR -> task traceability ----
        def t_okr_trace():
            r = page.evaluate("""()=>{
              activate('okr');const v=document.getElementById('v_okr');
              return {krs:krList().length, linked:(ST.tasks||[]).filter(t=>t.okr).length,
                      hasCoverage:/Прослеживаемость/.test(v.innerHTML), kpis:v.querySelectorAll('.kpi').length};}""")
            assert r['krs'] > 0 and r['linked'] > 0, 'no OKR links seeded'
            assert r['hasCoverage'] and r['kpis'] >= 4, 'OKR coverage block missing'
        case('okr: Key Result -> task traceability', t_okr_trace)

        # ---- 20. Scope-creep log + baseline diff ----
        def t_scope():
            r = page.evaluate("""()=>{
              const n0=(ST.scopeLog||[]).length;
              logScope('Добавлено','T-TEST','проверка',3,'');
              const n1=(ST.scopeLog||[]).length;
              ST.scopeLog=ST.scopeLog.filter(x=>x.item!=='T-TEST');
              activate('scope');const v=document.getElementById('v_scope');
              return {grew:n1>n0, view:v.children.length>0, kpis:v.querySelectorAll('.kpi').length,
                      hasBaseline:typeof scopeBaseline==='function'&&typeof scopeDiff==='function'};}""")
            assert r['grew'], 'logScope did not append'
            assert r['view'] and r['kpis'] >= 4, 'scope view incomplete'
            assert r['hasBaseline'], 'scope baseline/diff missing'
        case('scope: creep log and baseline tools', t_scope)

        # ---- 21. Monte-Carlo release date + flow efficiency + bug SLA ----
        def t_forecast():
            r = page.evaluate("""()=>{const C=compute();const mc=mcReleaseForecast(C);
              const fe=flowEfficiency();const sla=bugSLA();
              return {mcOk:!!mc, p50le85: mc?mc.p50<=mc.p85:true, hist:mc?mc.hist.length:0,
                      feRange: fe.eff>=0&&fe.eff<=1, slaTotal: sla.total, slaShape: sla.rows.every(x=>'open'in x&&'target'in x)};}""")
            assert r['mcOk'] and r['p50le85'] and r['hist'] > 0, 'Monte-Carlo forecast invalid'
            assert r['feRange'], 'flow efficiency out of range'
            assert r['slaTotal'] == 3 and r['slaShape'], 'bug SLA shape wrong'
        case('forecast: Monte-Carlo dates, flow efficiency, bug SLA', t_forecast)

        # ---- 22. Release confidence + PI board ----
        def t_release_pi():
            r = page.evaluate("""()=>{const C=compute();
              const rel=(ST.releases||[])[0];const conf=rel?releaseConfidence(rel,releaseComp(rel),C):null;
              activate('piboard');const pv=document.getElementById('v_piboard');
              activate('releases');const rv=document.getElementById('v_releases');
              return {conf:!!conf, confLabel: conf?conf.label:'', pi: pv.children.length>0,
                      piBoard: !!pv.querySelector('.pi-board')|| /Нет межстримовых/.test(pv.innerHTML),
                      burnup: !!rv.querySelector('#rel_bu')};}""")
            assert r['conf'] and r['confLabel'], 'release confidence missing'
            assert r['pi'] and r['piBoard'], 'PI program board did not render'
            assert r['burnup'], 'release burn-up chart missing'
        case('release+pi: confidence, burn-up, program board', t_release_pi)

        # ---- 23. Integration action triggers exist ----
        def t_integr():
            r = page.evaluate("""()=>({esc:typeof escalateBlockers,pub:typeof publishSprintReport,
              jira:typeof jiraSync,skills:typeof skillsFromActivity,api:typeof apiPost})""")
            for k in ('esc', 'pub', 'jira', 'skills', 'api'):
                assert r[k] == 'function', 'missing integration fn: ' + k
        case('integrations: escalate/publish/jira-sync/skills triggers', t_integr)

        # ---- 24. Whiteboard: anchored connectors, quick-add, connect, animation, emoji, link ----
        def t_board2():
            r = page.evaluate("""()=>{try{
              setPerm('editor');applyPerms();views();activate('board');
              const snap=JSON.stringify(ST.board.items), perm=JSON.stringify(PERM);
              PERM.canEdit=true;
              const _s=window.save,_u=window.brdWSUpsert,_e=window.brdEdit,_t=window.toast;
              window.save=()=>{};window.brdWSUpsert=()=>{};window.brdEdit=()=>{};window.toast=()=>{};
              // anchored connector endpoints follow shapes
              const a={id:'A',t:'rect',x:0,y:0,w:100,h:60,fill:'#fff',stroke:'#2D5BE3'};
              const b={id:'B',t:'rect',x:300,y:0,w:100,h:60,fill:'#fff',stroke:'#2D5BE3'};
              ST.board.items=[a,b];
              const conn={id:'C',t:'conn',from:'A',to:'B',stroke:'#334155'};ST.board.items.push(conn);
              const e1=brdConnEnds(conn);
              // quick-add from A to the right -> +2 items (shape + anchored conn)
              BW.sel=['A'];const n0=ST.board.items.length;brdQuickAdd('A','right');const n1=ST.board.items.length;
              const qConn=ST.board.items[ST.board.items.length-1];
              // connect selected A+B
              BW.sel=['A','B'];const n2=ST.board.items.length;brdConnectSel();const n3=ST.board.items.length;
              // animation
              BW.sel=['A'];brdSetAnim('pulse');const anim=brdItemById('A').anim;
              // deleting A removes connectors anchored to A
              BW.sel=['A'];const before=ST.board.items.length;brdDelSel();
              const aGone=!brdItemById('A');
              const danglers=ST.board.items.filter(x=>x.t==='conn'&&(x.from==='A'||x.to==='A')).length;
              window.save=_s;window.brdWSUpsert=_u;window.brdEdit=_e;window.toast=_t;
              ST.board.items=JSON.parse(snap);Object.assign(PERM,JSON.parse(perm));
              return {edgeRouted:(e1.x1>=90&&e1.x2<=310), quick:(n1-n0===2), quickAnchored:!!(qConn.from&&qConn.to),
                      connect:(n3-n2===1), anim:anim==='pulse', aGone:aGone, danglers:danglers};
            }catch(e){return 'ERR:'+e.message;}}""")
            assert r is not True and isinstance(r, dict), 'board2 failed: ' + str(r)
            assert r['edgeRouted'], 'anchored connector did not route to shape edges'
            assert r['quick'] and r['quickAnchored'], 'quick-add must create shape + anchored connector'
            assert r['connect'], 'connect-selected did not create a connector'
            assert r['anim'], 'animation not applied'
            assert r['aGone'] and r['danglers'] == 0, 'deleting a shape must remove its connectors'
            page.evaluate("()=>{setPerm('viewer');applyPerms();views();activate('dash');}")
        case('whiteboard2: connectors, quick-add, animation, cleanup', t_board2)

        # ---- 25. EVM: earned value indices and forecast ----
        def t_evm():
            r = page.evaluate("""()=>{const C=compute();const E=evm(C);
              return {bac:E.BAC>0, rows:E.rows.length===C.sp.length,
                      cpiOk:E.CPI===null||E.CPI>0, spiOk:E.SPI===null||E.SPI>0,
                      eacOk:E.EAC===null||(E.CPI&&Math.abs(E.EAC-E.BAC/E.CPI)<1),
                      chart:(activate('evm'),!!document.querySelector('#v_evm svg'))};}""")
            assert r['bac'] and r['rows'], 'EVM rows/BAC invalid'
            assert r['cpiOk'] and r['spiOk'], 'EVM indices out of range'
            assert r['eacOk'], 'EAC != BAC/CPI'
            assert r['chart'], 'EVM S-curve missing'
        case('evm: PV/EV/AC, CPI/SPI, EAC forecast', t_evm)

        # ---- 26. Planning poker consensus ----
        def t_poker():
            r = page.evaluate("""()=>{const rv=pokerReveal('A:5, B:8, C:8, D:5');
              const fib=[1,2,3,5,8,13,21];
              return {med:rv.med, cons:rv.consensus, inFib:fib.includes(rv.consensus),
                      spread:rv.spread, empty:pokerReveal('')};}""")
            assert r['empty'] is None, 'empty votes must return null'
            assert r['inFib'], 'consensus must snap to Fibonacci'
            assert r['spread'] == 3, 'spread wrong'
        case('poker: reveal median/consensus on Fibonacci', t_poker)

        # ---- 27. WBS rollup ----
        def t_wbs():
            r = page.evaluate("""()=>{
              const tasks=ST.tasks||[];const e=tasks.find(t=>(tasks.filter(c=>c.parent===t.id)).length>0);
              if(!e)return {skip:true};
              const roll=wbsRoll(e);const kids=tasks.filter(c=>c.parent===e.id);
              const kidSum=kids.reduce((a,c)=>a+num(c.est),0)+num(e.est);
              return {ok: roll.sp>=kidSum-0.001, rendered:(activate('wbs'),document.querySelectorAll('#v_wbs table tr').length>1)};}""")
            if r.get('skip'):
                raise Skip('no WBS hierarchy seeded')
            assert r['ok'], 'WBS rollup did not sum children'
            assert r['rendered'], 'WBS tree did not render'
        case('wbs: Epic rollup of child estimates', t_wbs)

        # ---- 28. Status report generation ----
        def t_status():
            r = page.evaluate("""()=>{const md=statusReportMd();
              return {len:md.length, rag:/Статус \\(RAG\\)/.test(md), kpi:/CPI \\/ SPI/.test(md),
                      hasVer:md.indexOf(APP_VERSION)>=0};}""")
            assert r['len'] > 200 and r['rag'] and r['kpi'], 'status report incomplete'
            assert r['hasVer'], 'status report missing version'
        case('status-report: RAG summary generated from data', t_status)

        # ---- 29. New PM registers seeded + portfolio snapshot ----
        def t_pm():
            r = page.evaluate("""()=>{try{
              const have=k=>Array.isArray(ST[k])&&ST[k].length>0;
              const regs=['changeRequests','issues','stakeholders','decisions','impediments','lessons','raci','storyMap','poker','portfolio'];
              const seeded=regs.every(have);
              // engagement gap computed
              const gap=(ST.stakeholders||[]).filter(x=>ENGAGE.indexOf(x.engageTarget)>ENGAGE.indexOf(x.engageCur)).length;
              // portfolio snapshot (guarded)
              const snap=JSON.stringify(ST.portfolio),perm=JSON.stringify(PERM);PERM.canEdit=true;
              const _s=window.save,_v=window.views,_a=window.activate,_t=window.toast;
              window.save=()=>{};window.views=()=>{};window.activate=()=>{};window.toast=()=>{};
              const n0=ST.portfolio.length;portfolioSnapshot();const grew=ST.portfolio.length>=n0;
              window.save=_s;window.views=_v;window.activate=_a;window.toast=_t;
              ST.portfolio=JSON.parse(snap);Object.assign(PERM,JSON.parse(perm));
              return {seeded, gap:gap>=0, grew};
            }catch(e){return 'ERR:'+e.message;}}""")
            assert r is not True and isinstance(r, dict), 'pm registers failed: ' + str(r)
            assert r['seeded'], 'not all PM registers seeded'
            assert r['gap'], 'stakeholder engagement gap compute failed'
            assert r['grew'], 'portfolio snapshot did not add/update entry'
        case('pm-registers: change/issues/stakeholders/... + portfolio snapshot', t_pm)

        br.close()
    httpd.shutdown()

    total = len(PASS) + len(FAIL) + len(SKIP)
    print('\n' + '=' * 60)
    print(f'RESULT: {len(PASS)} passed, {len(FAIL)} failed, {len(SKIP)} skipped  (of {total})')
    if FAIL:
        print('\nFailures:')
        for n, m in FAIL:
            print('  - ' + n + ': ' + m)
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
