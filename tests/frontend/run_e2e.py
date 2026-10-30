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

        # ---- 3b. assistant knows the whole app (self-training regression) ----
        def t_assistant():
            page.evaluate("()=>activate('dash')")
            r = page.evaluate("""()=>{
              if(typeof window.assistantAsk!=='function'||typeof window.assistantKB!=='function')
                return {err:'no assistant hooks (assistantAsk/assistantKB)'};
              const items=NAV.flatMap(g=>g.items);
              const ids=items.map(i=>i[0]);
              const KB=window.assistantKB();
              const missing=ids.filter(id=>!KB[id]||!KB[id].text||KB[id].text.length<8);
              const noanswer=[];
              items.forEach(it=>{const a=window.assistantAsk('что такое '+it[1]);
                if(!a||!a.t||a.t.length<8)noanswer.push(it[0]);});
              const ov=window.assistantAsk('какие разделы есть в приложении');
              const nw=window.assistantAsk('что нового в приложении');
              return {n:ids.length,kb:Object.keys(KB).length,missing:missing,noanswer:noanswer,
                      ovOK:!!(ov&&ov.t&&ov.t.indexOf('раздел')>=0),
                      nwOK:!!(nw&&nw.t&&nw.t.indexOf(APP_VERSION)>=0)};
            }""")
            assert 'err' not in r, r.get('err')
            assert r['kb'] == r['n'], 'KB covers %d of %d NAV sections' % (r['kb'], r['n'])
            assert not r['missing'], 'sections without knowledge text: %s' % r['missing']
            assert not r['noanswer'], 'sections the assistant cannot explain: %s' % r['noanswer']
            assert r['ovOK'], 'assistant overview («какие разделы есть») failed'
            assert r['nwOK'], 'assistant «что нового» missing current version'
        case('assistant: knows every NAV section (auto-trained)', t_assistant)

        # ---- 3c. resizable table columns (grips + persist) ----
        def t_colresize():
            page.evaluate("()=>activate('sprintGoals')"); page.wait_for_timeout(200)
            r = page.evaluate("""()=>{
              if(typeof window.__colResizeEnhance!=='function')return {err:'no colResize hook'};
              const t=document.querySelector('#v_sprintGoals table');
              if(!t)return {err:'no table'};
              window.__colResizeEnhance(t);
              const hr=(t.tHead&&t.tHead.rows[0])||t.rows[0];
              const cols=hr.cells.length;
              const grips=t.querySelectorAll('.col-grip').length;
              const widthsSet=[].every.call(hr.cells,c=>/px|%/.test(c.style.width||''));
              const fixed=t.classList.contains('colr');
              // идемпотентность: второй вызов не плодит гриппы
              window.__colResizeEnhance(t);
              const grips2=t.querySelectorAll('.col-grip').length;
              return {cols:cols,grips:grips,grips2:grips2,widthsSet:widthsSet,fixed:fixed};
            }""")
            assert 'err' not in r, r.get('err')
            assert r['cols'] >= 2, 'table has too few columns'
            assert r['grips'] == r['cols'] - 1, 'grips %d != cols-1 (%d)' % (r['grips'], r['cols'] - 1)
            assert r['grips2'] == r['grips'], 'enhance is not idempotent (%d -> %d)' % (r['grips'], r['grips2'])
            assert r['widthsSet'], 'column widths were not frozen'
            assert r['fixed'], 'table did not switch to fixed layout (.colr)'
            # grips must survive an in-place re-render (sort/filter)
            page.evaluate("()=>activate('team')"); page.wait_for_timeout(250)
            r2 = page.evaluate("""()=>{
              const t=document.querySelector('#v_team table'); if(!t)return {skip:true};
              window.__colResizeEnhance(t);
              const hr=(t.tHead&&t.tHead.rows[0])||t.rows[0];
              const th=hr.querySelector('th.sortable'); if(!th)return {skip:true};
              const before=t.querySelectorAll('.col-grip').length;
              th.click();  // sort → re-render thead/tbody in place
              return {before:before};
            }""")
            if not r2.get('skip'):
                page.wait_for_timeout(300)  # allow MO debounce + repair
                after = page.evaluate("()=>{const t=document.querySelector('#v_team table');"
                                      "const hr=(t.tHead&&t.tHead.rows[0])||t.rows[0];"
                                      "return {grips:t.querySelectorAll('.col-grip').length,need:hr.cells.length-1};}")
                assert after['grips'] == after['need'], \
                    'grips lost after sort: %d != %d' % (after['grips'], after['need'])
        case('tables: columns are resizable (grips survive sort/filter)', t_colresize)

        # ---- 3d. JSON import normalizes partial data via migrate() ----
        def t_import_migrate():
            page.evaluate("()=>activate('dash')")
            r = page.evaluate("""()=>{
              const backup=JSON.stringify(ST);
              try{
                // частичный «импорт»: только params + одна задача, без большинства коллекций/досок
                const partial={params:JSON.parse(backup).params,
                               tasks:[{id:'T-99',title:'x',role:'Backend',type:'Задача',est:3,status:'To Do',sprint:1}]};
                ST=migrate(JSON.parse(JSON.stringify(partial)));
                const need=['team','tasks','boards','risks','bugs','deps','releases',
                            'incidents','deployments','stakeholders','okr'];
                const missing=need.filter(k=>!Array.isArray(ST[k]));
                if(!ST.board||typeof ST.board!=='object')missing.push('board');
                let threw=null;
                try{views();activate('team');activate('dora');activate('kanban');activate('dash');}
                catch(e){threw=String((e&&e.message)||e);}
                return {missing:missing,threw:threw};
              } finally { ST=JSON.parse(backup); try{views();activate('dash');}catch(e){} }
            }""")
            assert not r['missing'], 'migrate() left collections missing after partial import: %s' % r['missing']
            assert not r['threw'], 'views() threw after migrated partial import: %s' % r['threw']
        case('import: partial JSON is normalized by migrate() without crashing', t_import_migrate)

        # ---- 3e. Ishikawa fishbone is data-driven + editable ----
        def t_ishikawa():
            page.evaluate("()=>activate('risks')"); page.wait_for_timeout(250)
            r = page.evaluate("""()=>{
              const box=document.getElementById('ishk'); if(!box)return {err:'no #ishk'};
              if(!box.querySelector('svg'))return {err:'no svg'};
              const cats=(ST.ishikawaCats||[]).length, causes=(ST.ishikawa||[]).length;
              if(!Array.isArray(ST.ishikawa))ST.ishikawa=[];
              const catName=((ST.ishikawaCats||[])[0]||{}).name||'Люди';
              ST.ishikawa.push({id:'IC-TEST',cat:catName,cause:'ТЕСТ_ПРИЧИНА_XYZ',weight:9,risk:''});
              drawIshikawa(box);
              const txt=[].map.call(box.querySelectorAll('text'),t=>t.textContent).join('|');
              const has=txt.indexOf('ТЕСТ_ПРИЧИНА_XYZ')>=0;
              const weightShown=txt.indexOf('ТЕСТ_ПРИЧИНА_XYZ [9]')>=0;
              ST.ishikawa=ST.ishikawa.filter(x=>x.id!=='IC-TEST');drawIshikawa(box); // cleanup
              const tables=document.querySelectorAll('#v_risks table').length;
              return {cats:cats,causes:causes,has:has,weightShown:weightShown,tables:tables};
            }""")
            assert 'err' not in r, r.get('err')
            assert r['cats'] >= 1 and r['causes'] >= 1, 'ishikawa seed missing (cats=%s causes=%s)' % (r['cats'], r['causes'])
            assert r['has'], 'new cause not drawn on the fishbone after drawIshikawa()'
            assert r['weightShown'], 'cause weight is not shown on the diagram'
            assert r['tables'] >= 3, 'risks view should expose risks + ishikawa + categories tables (got %d)' % r['tables']
        case('ishikawa: fishbone is data-driven and editable', t_ishikawa)

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
            page.evaluate("()=>{try{localStorage.removeItem('navui');}catch(e){}NAVS.mode='all';buildNav();}")
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
              NAVS.mode='compact';buildNav();
              return {hasSearch,fav,pinned,toggled,matches};}""")
            assert r['hasSearch'], 'nav search box missing'
            assert r['fav'] and r['pinned'], 'pin → favorites did not work'
            assert r['toggled'], 'group collapse toggle did not work'
            assert r['matches'] == ['Гант', 'Гант по иерархии'], 'filter did not narrow to the matches: ' + str(r['matches'])
        case('sidebar: collapse/pin/filter smart nav', t_nav)

        # ---- 4f. Top toolbar: data actions consolidated into one menu ----
        def t_toolbar():
            r = page.evaluate("""()=>{
              const visible=[...document.querySelector('.tools').children].filter(c=>c.offsetParent!==null).map(c=>c.id);
              document.getElementById('ubtn').click();
              const opened=document.getElementById('umenu').classList.contains('open');
              const items=[...document.querySelectorAll('#upop .btn')].map(b=>b.id);
              document.body.click();
              const closed=!document.getElementById('umenu').classList.contains('open');
              return {visible,opened,items,closed};}""")
            assert all(x in r['visible'] for x in ('qcdm', 'stdot', 'umenu')), 'compact header: ＋ Создать, status dot, user menu: ' + str(r['visible'])
            for x in ('profbtn', 'rolebtn', 'tourbtn', 'logoutbtn'):
                assert x in r['items'], 'user menu missing ' + x
            for x in ('themebtn', 'densbtn', 'startbtn'):
                assert x not in r['items'], x + ' moved to «Мой профиль», not the menu'
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

        # ---- 24b. Whiteboard tools: ergonomics, live data, templates ----
        def t_board3():
            r = page.evaluate("""()=>{try{
              setPerm('editor');applyPerms();views();activate('board');
              const snap=JSON.stringify(ST.board.items), perm=JSON.stringify(PERM);
              const keep={};['tasks','risks','impediments','decisions','retro','lessons'].forEach(k=>keep[k]=JSON.stringify(ST[k]||[]));
              PERM.canEdit=true;
              const _s=window.save,_u=window.brdWSUpsert,_e=window.brdEdit,_t=window.toast,_f=window.brdFocusBox;
              window.save=()=>{};window.brdWSUpsert=()=>{};window.brdEdit=()=>{};window.toast=()=>{};
              const out={};
              // --- отмена / повтор ---
              ST.board.items=[];brdHistReset();
              brdAdd({id:'S1',t:'sticky',x:0,y:0,w:150,h:120,fill:'#FFE066',text:'Идея альфа',author:'t',votes:0});brdSave();
              const nA=brdItems().length;brdUndo();const nU=brdItems().length;brdRedo();const nR=brdItems().length;
              out.undo=(nA===1&&nU===0&&nR===1);
              // --- копировать/вставить: связь между копиями перепривязывается ---
              brdAdd({id:'R1',t:'rect',x:300,y:0,w:100,h:60,fill:'#fff',stroke:'#2D5BE3'});brdAdd({id:'K1',t:'conn',from:'S1',to:'R1',stroke:'#334155'});
              BW.sel=['S1','R1'];brdCopy(true);brdPaste();
              const pasted=brdItems().filter(x=>['S1','R1','K1'].indexOf(x.id)<0),pc=pasted.find(x=>x.t==='conn');
              out.paste=(pasted.length===3&&!!pc&&pasted.some(x=>x.id===pc.from)&&pasted.some(x=>x.id===pc.to));
              ST.board.items=brdItems().filter(x=>['S1','R1','K1'].indexOf(x.id)>=0);
              // --- группа: клик по одному элементу выделяет всю группу ---
              BW.sel=['S1','R1'];brdGroup();BW.sel=[];brdSelectWith('S1',false);out.group=(BW.sel.length===2);brdUngroup();
              // --- выравнивание и распределение ---
              brdItemById('R1').y=200;BW.sel=['S1','R1'];brdAlign('top');out.align=(brdItemById('R1').y===brdItemById('S1').y);
              ST.board.items=[{id:'D1',t:'rect',x:0,y:0,w:100,h:60},{id:'D2',t:'rect',x:50,y:0,w:100,h:60},{id:'D3',t:'rect',x:500,y:0,w:100,h:60}];
              BW.sel=['D1','D2','D3'];brdDistribute('h');out.distribute=(Math.abs(brdItemById('D2').x-250)<0.01);
              // --- закрепление: не удаляется и не двигается ---
              ST.board.items=[{id:'L1',t:'sticky',x:0,y:0,w:100,h:100,text:'фикс',locked:true}];
              BW.sel=['L1'];brdDelSel();out.lockDel=!!brdItemById('L1');out.lockMove=(brdMoveSet().indexOf('L1')<0);
              // --- фрейм переносится вместе с содержимым ---
              ST.board.items=[{id:'F1',t:'frame',x:0,y:0,w:600,h:400,title:'F'},{id:'S9',t:'sticky',x:100,y:100,w:120,h:100,text:'внутри'},{id:'S8',t:'sticky',x:900,y:900,w:120,h:100,text:'снаружи'}];
              BW.sel=['F1'];const ms=brdMoveSet();out.frameCarries=(ms.indexOf('S9')>=0&&ms.indexOf('S8')<0);
              // --- сетка, мини-карта, поиск ---
              const sn0=BW.snap;BW.snap=true;out.snap=(brdSnapV(30)===22&&brdSnapV(40)===44);BW.snap=sn0;
              const mm=document.getElementById('brd-mini');if(mm)mm.style.display='';brdMiniRender();
              out.minimap=!!mm&&mm.querySelectorAll('rect').length>=3;
              out.search=(brdFind('внутри').length===1&&brdFind('несуществующее-xyz').length===0);
              // --- живая карточка задачи + смена статуса из доски ---
              ST.board.items=[];const t0=ST.tasks[0],st0=t0.status;
              const card=brdAddTaskCard(t0.id);brdRender();
              out.taskCard=!!card&&document.querySelector('#v_board svg').textContent.indexOf(t0.id)>=0;
              brdTaskCycle(card.id);out.taskCycle=(t0.status!==st0);
              t0.title=t0.title+' (обновлено)';brdRender();out.taskLive=document.querySelector('#v_board svg').textContent.indexOf('(обновлено)')>=0;
              // --- виджеты-метрики ---
              let mOk=true;BRD_METRICS.forEach(m=>{const d=brdMetricData(m[0]);if(!d||!d.title||(d.val==null&&d.text==null))mOk=false;});
              brdAddMetric('velocity');brdRender();out.metric=mOk&&document.querySelector('#v_board svg').textContent.indexOf('VELOCITY')>=0;
              // --- стикер -> сущность ---
              ST.board.items=[{id:'C1',t:'sticky',x:0,y:0,w:150,h:120,text:'Риск сбоя оплаты'},{id:'C2',t:'sticky',x:0,y:200,w:150,h:120,text:'Сделать экспорт CSV'},{id:'C3',t:'sticky',x:0,y:400,w:150,h:120,text:'Нет доступа к стенду'}];
              const nr=(ST.risks||[]).length,nt=(ST.tasks||[]).length,ni=(ST.impediments||[]).length;
              BW.sel=['C1'];brdConvert('risk');BW.sel=['C2'];brdConvert('task');BW.sel=['C3'];brdConvert('impediment');
              out.convRisk=(ST.risks.length===nr+1&&brdItemById('C1').ref.k==='risk');
              out.convTask=(ST.tasks.length===nt+1&&brdItemById('C2').t==='task'&&!!brdTask(brdItemById('C2')));
              out.convImp=(ST.impediments.length===ni+1&&/^IM-/.test(brdItemById('C3').ref.id));
              // --- шаблоны: каждый добавляет сгруппированную сетку фреймов ---
              ST.board.items=[];let tplOk=true;
              Object.keys(BRD_TPL).forEach(k=>{const before=brdItems().length,made=brdInsertTemplate(k)||[];const frames=made.map(brdItemById).filter(x=>x&&x.t==='frame');
                if(brdItems().length<=before||frames.length<BRD_TPL[k].cells.length+1||!frames.every(f=>f.grp===frames[0].grp))tplOk=false;});
              out.templates=tplOk&&Object.keys(BRD_TPL).length>=11;
              const outer=brdItems().find(x=>x.t==='frame'&&x.title.indexOf(BRD_TPL.ssc.name)>=0);BW.sel=[];brdSelectWith(outer.id,false);
              out.tplMoveAll=(BW.sel.length===4&&brdMoveSet().length>=7);
              // восстановление
              window.save=_s;window.brdWSUpsert=_u;window.brdEdit=_e;window.toast=_t;
              ST.board.items=JSON.parse(snap);Object.keys(keep).forEach(k=>ST[k]=JSON.parse(keep[k]));Object.assign(PERM,JSON.parse(perm));BW.sel=[];brdHistReset();brdRender();
              return out;
            }catch(e){return 'ERR:'+e.message+' '+(e.stack||'').split('\\n')[1];}}""")
            assert isinstance(r, dict), r
            bad = [k for k, v in r.items() if v is not True]
            assert not bad, 'board tools failed checks: %s (%s)' % (bad, r)
        case('whiteboard3: undo/clipboard/group/align/lock, live tasks & metrics, sticky->entity, templates', t_board3)

        # ---- 24c. Whiteboard wave 2: sessions (vote/anon/present/comments) + diagrams ----
        def t_board4():
            r = page.evaluate("""()=>{try{
              setPerm('editor');applyPerms();views();activate('board');
              const snap=JSON.stringify(ST.board.items),sess=JSON.stringify(ST.board.session||null),perm=JSON.stringify(PERM);
              PERM.canEdit=true;
              const _s=window.save,_u=window.brdWSUpsert,_e=window.brdEdit,_t=window.toast,_w=window.brdWSSend,_c=window.confirm;
              window.save=()=>{};window.brdWSUpsert=()=>{};window.brdEdit=()=>{};window.toast=()=>{};window.brdWSSend=()=>{};
              const out={};const txt=()=>document.querySelector('#v_board svg').textContent;
              // --- голосование точками: лимит, скрытый режим, раскрытие, медали, снятие голоса ---
              ST.board.items=[{id:'V1',t:'sticky',x:0,y:0,w:150,h:120,text:'Идея A',author:'Петров',votes:0},{id:'V2',t:'sticky',x:200,y:0,w:150,h:120,text:'Идея B',author:'Петров',votes:0}];
              ST.board.session={};brdSessSet(s=>{s.vote={on:true,limit:2,hidden:true,revealed:false};});
              const a1=brdVote('V1'),a2=brdVote('V1'),a3=brdVote('V2');
              out.voteLimit=(a1&&a2&&!a3&&brdVoteLeft()===0&&brdItemById('V1').votes===2);
              out.voteHidden=(brdVoteLabel(brdItemById('V1'))==='✓2'&&brdVoteLabel(brdItemById('V2'))==='🗳');
              brdVote('V1',true);out.unvote=(brdItemById('V1').votes===1&&brdVoteLeft()===1);
              brdVote('V1');brdSessSet(s=>{s.vote.revealed=true;});brdRender();
              out.reveal=(brdVoteLabel(brdItemById('V1'))==='👍2'&&brdVoteRanks()['V1']===1&&txt().indexOf('🥇')>=0);
              brdVoteReset(true);out.voteReset=(!brdItemById('V1').votes&&!brdItemById('V1').voters&&!brdSess().vote.revealed);
              // --- анонимный ввод ---
              brdSessSet(s=>{s.anon=true;s.anonRevealed=false;});const hid=brdAuthorLabel(brdItemById('V1'));
              brdSessSet(s=>{s.anonRevealed=true;});out.anon=(hid.indexOf('Петров')<0&&brdAuthorLabel(brdItemById('V1')).indexOf('Петров')>=0);
              brdSessSet(s=>{s.anon=false;});
              // --- показ по фреймам: порядок чтения, листание, выход ---
              ST.board.items=[{id:'P2',t:'frame',x:900,y:0,w:400,h:300,title:'Второй'},{id:'P1',t:'frame',x:0,y:0,w:400,h:300,title:'Первый'},
                {id:'P1a',t:'frame',x:20,y:40,w:100,h:100,title:'вложенный'},{id:'P3',t:'frame',x:0,y:700,w:400,h:300,title:'Третий'}];
              const order=brdPresFrames().map(f=>f.id).join(',');out.presOrder=(order==='P1,P2,P3');
              brdPresStart();const on=BW.wrap.classList.contains('brd-presenting')&&BW.pres.i===0;brdPresGo(1);const i1=BW.pres.i;brdPresGo(99);const iEnd=BW.pres.i;
              brdPresEnd();out.present=(on&&i1===1&&iEnd===2&&!BW.pres&&!BW.wrap.classList.contains('brd-presenting'));
              // --- комментарии с @упоминаниями ---
              const who=(ST.team[0]||{}).name;ST.board.items=[{id:'M1',t:'sticky',x:0,y:0,w:150,h:120,text:'Обсудить'}];
              const cm=brdCmtAdd('M1','Посмотри, пожалуйста @'+who);brdRender();
              out.comment=(!!cm&&cm.m.indexOf(who)>=0&&brdItemById('M1').comments.length===1&&txt().indexOf('💬 1')>=0&&brdCmtAll().length===1&&brdFind('Посмотри').length===1);
              brdCmtDel('M1',cm.id);out.commentDel=!brdItemById('M1').comments;
              // --- блок-схема: новые фигуры + подпись стрелки + быстрое продолжение ---
              ST.board.items=[];let shapes=true;['terminator','document','database','parallelogram'].forEach((t,i)=>{brdAdd({id:'F'+i,t:t,x:i*220,y:0,w:160,h:90,fill:'#fff',stroke:'#2D5BE3',text:t});});
              brdRender();['F0','F1','F2','F3'].forEach(id=>{const g=document.querySelector('#v_board svg [data-id="'+id+'"]');if(!g||!g.querySelector('path,polygon,rect'))shapes=false;});
              brdAdd({id:'K1',t:'conn',from:'F0',to:'F1',label:'да'});brdRender();
              out.flow=shapes&&txt().indexOf('да')>=0&&BRD_DRAW_T.indexOf('database')>=0;
              const nq=brdItems().length;brdQuickAdd('F0','down');out.flowQuick=(brdItems().length===nq+2&&brdItems()[brdItems().length-2].t==='terminator');
              // --- майнд-карта: дочерние/соседние ветки, раскладка в обе стороны, удаление ветки целиком ---
              ST.board.items=[];const root=brdMindNew();const c1=brdMindAdd(root.id,'child',true),c2=brdMindAdd(root.id,'child',true),s1=brdMindAdd(c1.id,'sibling',true),g1=brdMindAdd(c1.id,'child',true);
              const R=brdItemById(root.id);
              out.mindTree=(brdMindKids(root.id).length===3&&c1.x>R.x+R.w&&c2.x+c2.w<R.x&&g1.x>c1.x+c1.w&&brdMindRoot(g1.id).id===root.id);
              out.mindConn=brdItems().filter(x=>x.t==='conn'&&x.style==='mind').length===4;
              BW.sel=[c1.id];brdDelSel();out.mindDel=(!brdItemById(g1.id)&&!!brdItemById(c2.id)&&brdItems().filter(x=>x.t==='conn').length===2);
              // --- таблица: ячейки, строки, столбцы ---
              ST.board.items=[];const tb=brdTableNew();brdTableSet(tb.id,1,0,'Риск');const h0=tb.h,w0=tb.w;
              brdTableOp('addRow',tb.id);brdTableOp('addCol',tb.id);brdRender();
              const T=brdItemById(tb.id);out.table=(T.rows.length===4&&T.rows[0].length===4&&T.h>h0&&T.w>w0&&T.rows[1][0]==='Риск'&&txt().indexOf('Риск')>=0);
              brdTableOp('delRow',tb.id);brdTableOp('delCol',tb.id);out.tableDel=(brdItemById(tb.id).rows.length===3&&brdItemById(tb.id).rows[0].length===3);
              // --- авто-раскладка: сетка и дерево по связям ---
              ST.board.items=[{id:'A',t:'rect',x:0,y:0,w:100,h:60},{id:'B',t:'rect',x:500,y:400,w:100,h:60},{id:'C',t:'rect',x:40,y:900,w:100,h:60},{id:'E1',t:'conn',from:'A',to:'B'},{id:'E2',t:'conn',from:'A',to:'C'}];
              BW.sel=['A','B','C'];brdAutoTree();const A=brdItemById('A'),B=brdItemById('B'),Cc=brdItemById('C');
              out.autoTree=(B.x>A.x+A.w&&B.x===Cc.x&&B.y!==Cc.y);
              ST.board.items=[0,1,2,3].map(i=>({id:'G'+i,t:'rect',x:i*13,y:i*500,w:100,h:60}));BW.sel=['G0','G1','G2','G3'];brdAutoGrid();
              const xs=new Set(brdItems().map(x=>x.x)),ys=new Set(brdItems().map(x=>x.y));out.autoGrid=(xs.size===2&&ys.size===2);
              // --- шаблон дорожек по ролям команды ---
              ST.board.items=[];const roles=new Set((ST.team||[]).map(m=>m.role).filter(Boolean)).size;brdInsertTemplate('swim');
              out.swim=brdItems().filter(x=>x.t==='frame'&&x.notitle).length===Math.min(6,roles||4);
              // восстановление
              window.save=_s;window.brdWSUpsert=_u;window.brdEdit=_e;window.toast=_t;window.brdWSSend=_w;window.confirm=_c;
              ST.board.items=JSON.parse(snap);ST.board.session=JSON.parse(sess)||{};Object.assign(PERM,JSON.parse(perm));BW.sel=[];BW.pres=null;brdHistReset();brdRender();
              return out;
            }catch(e){return 'ERR:'+e.message+' '+(e.stack||'').split('\\n')[1];}}""")
            assert isinstance(r, dict), r
            bad = [k for k, v in r.items() if v is not True]
            assert not bad, 'board wave-2 checks failed: %s (%s)' % (bad, r)
        case('whiteboard4: voting/anon/presentation/comments, flowchart, mind map, table, auto-layout, swimlanes', t_board4)

        # ---- 25. EVM: earned value indices and forecast ----
        def t_evm():
            r = page.evaluate("""async()=>{const C=compute();const E=evm(C);activate('evm');await new Promise(r=>setTimeout(r,60));
              return {bac:E.BAC>0, rows:E.rows.length===C.sp.length,
                      cpiOk:E.CPI===null||E.CPI>0, spiOk:E.SPI===null||E.SPI>0,
                      eacOk:E.EAC===null||(E.CPI&&Math.abs(E.EAC-E.BAC/E.CPI)<1),
                      chart:!!document.querySelector('#v_evm svg')};}""")
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

        # ---- Hierarchical Gantt: Epic → Feature → Story → Task by «parent», rollup of volume and progress ----
        def t_hgantt():
            r = page.evaluate("""()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             const keep=JSON.stringify(ST.tasks);
             try{HG.level=2;HG.open={};HG.fact=true;views();activate('hgantt');
              const tabs=[...document.querySelectorAll('#v_hgantt > .hub-tabs [data-hubv]')].map(b=>b.dataset.hubv);
              const T=ST.tasks,types=[...new Set(T.map(t=>t.type))];
              const rows=()=>[...document.querySelectorAll('#hg_root .hg-row[data-hgrow]')].map(x=>x.dataset.hgrow);
              const l2=rows(),roots=T.filter(t=>!t.parent||!T.some(x=>x.id===t.parent)).map(t=>t.id),feats=T.filter(t=>t.type==='Фича').map(t=>t.id);
              const lvl2=roots.every(id=>l2.includes(id))&&feats.every(id=>l2.includes(id))&&!l2.includes('T-02');
              document.querySelector('#hg_root [data-hglv="1"]').click();const l1=rows();
              document.querySelector('#hg_root [data-hgt="E-1"]').click();const e1open=rows().includes('FE-1')&&!rows().includes('FE-3');
              document.querySelector('#hg_root [data-hglv="9"]').click();const l9=rows().length;
              const desc=id=>{const out=[];const go=q=>T.filter(t=>t.parent===q).forEach(c=>{out.push(c);go(c.id);});go(id);return out;};
              const all=[T.find(t=>t.id==='E-1')].concat(desc('E-1'));
              const sp=all.reduce((s,t)=>s+num(t.est),0),dn=all.filter(t=>t.status==='Готово').reduce((s,t)=>s+num(t.est),0);
              const meta=document.querySelector('#hg_root [data-hgrow="E-1"] .hg-m').textContent;
              const G=hgTree(),n=G.nodes.find(x=>x.t.id==='E-1'),ks=desc('E-1').map(t=>num(t.sprint)).filter(s=>s>0);
              const roll=n.sp===sp&&n.done===dn&&+n.a===+G.spA(Math.min(...ks))&&+n.b===+addD(G.spA(Math.max(...ks)),11);
              const late=[...document.querySelectorAll('#hg_root .hg-late')].map(x=>x.closest('[data-hgrow]').dataset.hgrow);
              const facts=document.querySelectorAll('#hg_root .hg-f').length;
              document.querySelector('#hg_root [data-hgf]').click();const noFact=document.querySelectorAll('#hg_root .hg-f').length===0;HG.fact=true;
              const a=T.find(t=>t.id==='T-19'),b=T.find(t=>t.id==='T-20'),pa=a.parent,pb=b.parent;a.parent='T-20';b.parent='T-19';hgRefresh();
              const cyc=(document.querySelector('#hg_root .wiz-warn:not(.hg-linkbad)')||{}).textContent||'';a.parent=pa;b.parent=pb;hgRefresh();
              document.querySelector('#hg_root [data-hgo="T-14"]').click();const opened=CURV==='backlog'&&UI.search.tasks==='T-14';UI.search.tasks='';
              const again=migrate(JSON.parse(JSON.stringify(ST))).tasks.filter(t=>t.type==='Фича').length;
              const blank=migrate(%(BLANK)s(ST)).tasks.length;
              return {tabs,types,lvl2,l1,roots,e1open,l9,n:T.length,meta,roll,late,facts,noFact,cyc,opened,again,feats:feats.length,blank,depth:wbsDepth(T.filter(t=>!t.parent),T),errs};
             }catch(e){return 'ERR:'+e.message;}finally{window.removeEventListener('error',h);ST.tasks=JSON.parse(keep);HG.level=2;HG.open={};HG.fact=true;views();activate('dash');}}""" % {'BLANK': 'blankState'})
            assert isinstance(r, dict), 'hgantt failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['tabs'][:2] == ['gantt', 'hgantt'], 'hierarchical Gantt is a tab of «Расписание»: ' + str(r['tabs'])
            assert r['depth'] >= 4 and {'Эпик', 'Фича', 'История', 'Задача'} <= set(r['types']) and r['feats'] == 4, 'demo has 4 levels: ' + str(r)
            assert r['lvl2'], 'level «До фич» shows roots and features, hides stories/tasks'
            assert set(r['l1']) == set(r['roots']) and r['e1open'], 'level «Эпики» + expanding one epic: ' + str(r['l1'])
            assert r['l9'] == r['n'], 'level «Всё» shows every element once'
            assert r['roll'] and 'SP' in r['meta'], 'epic rollup: volume, done and span from descendants: ' + str(r['meta'])
            assert 'T-12' in r['late'] and 'T-10' in r['late'], 'overdue / out-of-sprint elements outlined: ' + str(r['late'])
            assert r['facts'] > 0 and r['noFact'], 'fact bars toggle'
            assert 'цикле' in r['cyc'], 'cycle in «Родитель» is reported, not crashing'
            assert r['opened'], 'ID opens the element in «Бэклог»'
            assert r['again'] == 4 and r['blank'] == 0, 'demo features added once; blank project gets none: ' + str(r)
        case('hgantt: hierarchy Gantt — levels, rollup, plan/fact, overdue, cycles, demo features', t_hgantt)

        # ---- Stage marks on the hierarchy Gantt: auto by roles/demo/release, manual panel, legend, role mapping ----
        def t_stages():
            r = page.evaluate("""()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             const keepT=JSON.stringify(ST.tasks),keepR=ST.params.stageRoles;
             try{setPerm('editor');applyPerms();HG.level=9;HG.open={};HG.marks=true;views();activate('hgantt');
              const leg=document.querySelectorAll('#hg_root .hg-mleg .hg-mi').length,legTxt=(document.querySelector('#hg_root .hg-mleg')||{}).textContent||'';
              const n=id=>hgFind(id),t1=n('T-01'),f1=n('FE-1');
              const auto={dev:[t1.st.dev_s,t1.st.dev_e],psi:[t1.st.psi_s,t1.st.psi_e],prod:[t1.st.prod_s,t1.st.prod_e],
               feDevS:f1.st.dev_s,feDevE:f1.st.dev_e||null,feBa:[f1.st.ba_s,f1.st.ba_e],feMan:Object.keys(f1.mk).sort()};
              const t1marks=document.querySelectorAll('#hg_root [data-hgrow="T-01"] .hg-mk').length;
              const shapes=[...document.querySelectorAll('#hg_root [data-hgrow="T-01"] .hg-mk')].map(m=>m.title.split(' — ')[0]);
              // ручная метка: панель «Этапы» по клику на название
              document.querySelector('#hg_root [data-hgrow="T-12"] .hg-tt').click();const m=document.getElementById('hgsmodal');
              const fields=m.querySelectorAll('[data-hgk]').length;m.querySelector('[data-hgk="ba_s"]').value='2026-08-20';m.querySelector('[data-hgsx=ok]').click();
              const saved=JSON.stringify(ST.tasks.find(x=>x.id==='T-12').stages),manMk=[...document.querySelectorAll('#hg_root [data-hgrow="T-12"] .hg-mk')].some(x=>/вручную/.test(x.title)&&x.querySelector('svg circle[r="1.9"]'));
              document.querySelector('#hg_root [data-hgrow="T-12"] .hg-mk').click();document.querySelector('#hgsmodal [data-hgsx=auto]').click();
              const reset=JSON.stringify(ST.tasks.find(x=>x.id==='T-12').stages);
              // роли: убираем Backend из разработки — авто-метки разработки у T-01 пропадают
              ST.params.stageRoles='ba=Product Owner;sa=Analyst;dev=Frontend;ift=QA';const noDev=!hgFind('T-09').st.dev_s&&!hgFind('T-01').st.dev_s&&!!hgFind('T-02').st.dev_s;ST.params.stageRoles=keepR;
              activate('params');const roleBoxes=document.querySelectorAll('#hgrdiv [data-hgr]').length;
              const cb=document.querySelector('#hgrdiv [data-hgr="ift"][value="DevOps"]');cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));
              const mapped=(hgRoleMap().ift||[]).includes('DevOps');ST.params.stageRoles=keepR;
              // просмотр: панель только для чтения
              setPerm('viewer');applyPerms();activate('hgantt');document.querySelector('#hg_root [data-hgrow="T-01"] .hg-tt').click();
              const ro=[...document.querySelectorAll('#hgsmodal [data-hgk]')].every(i=>i.disabled)&&!document.querySelector('#hgsmodal [data-hgsx=ok]');
              document.querySelector('#hgsmodal [data-hgsx=cancel]').click();setPerm('editor');applyPerms();
              document.querySelector('#hg_root [data-hgm]').click();const hidden=document.querySelectorAll('#hg_root .hg-mk').length===0;HG.marks=true;
              return {leg,legTxt,auto,t1marks,shapes,fields,saved,manMk,reset,noDev,roleBoxes,mapped,ro,hidden,errs};
             }catch(e){return 'ERR:'+e.message+' '+e.stack;}finally{window.removeEventListener('error',h);ST.tasks=JSON.parse(keepT);ST.params.stageRoles=keepR;HG.marks=true;HG.level=2;HG.open={};setPerm('editor');applyPerms();views();activate('dash');}}""")
            assert isinstance(r, dict), 'stages failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['leg'] == 12 and 'Контур — начало' in r['legTxt'], 'legend lists all 12 marks with description'
            a = r['auto']
            assert a['dev'] == ['2026-08-03', '2026-08-06'], 'dev marks of T-01 from role Backend dates: ' + str(a)
            assert a['psi'] == ['2026-08-14', '2026-08-14'], 'PSI from accepted sprint demo: ' + str(a)
            assert a['prod'] == ['2026-08-17', '2026-08-28'], 'Prod from release R-1 (done): ' + str(a)
            assert a['feDevS'] == '2026-08-03' and a['feDevE'] is None, 'parent: earliest start, no end while a child is not done: ' + str(a)
            assert a['feBa'] == ['2026-07-20', '2026-07-24'] and a['feMan'] == ['ba_e', 'ba_s', 'sa_e', 'sa_s'], 'demo manual analysis marks: ' + str(a)
            assert r['t1marks'] >= 6 and 'Начало разработки' in r['shapes'] and 'Выход в Прод' in r['shapes'], str(r['shapes'])
            assert r['fields'] == 12 and r['saved'] == '{"ba_s":"2026-08-20"}' and r['manMk'], 'manual mark via panel: ' + str(r)
            assert r['reset'] == '{}', 'reset to auto clears manual marks'
            assert r['noDev'], 'role mapping drives auto marks'
            assert r['roleBoxes'] == 4 * 8 and r['mapped'], 'role mapping editable in Parameters: ' + str(r)
            assert r['ro'] and r['hidden'], 'viewer read-only panel; marks toggle'
        case('stages: hierarchy Gantt stage marks — auto (roles, demo, release), manual panel, legend, roles', t_stages)

        # ---- Regression: stage panel rows stay aligned (hint «авто: дата · сегодня» never wraps) ----
        def t_stpanel_layout():
            r = page.evaluate("""async()=>{try{setPerm('editor');applyPerms();HG.level=9;views();activate('hgantt');hgStagesOpen('T-16');const box=document.querySelector('#hgsmodal .mbox'),out=[];
              for(const w of [420,512,560]){box.style.width=w+'px';await new Promise(r=>setTimeout(r,30));
               document.querySelectorAll('#hgsmodal .hgs-n').forEach(n=>{const s=n.nextElementSibling,e=s.nextElementSibling;
                out.push([w,Math.round(e.querySelector('input').getBoundingClientRect().top-s.querySelector('input').getBoundingClientRect().top),
                 Math.max(s.querySelector('.hgs-h').getBoundingClientRect().height,e.querySelector('.hgs-h').getBoundingClientRect().height)]);});}
              return out;}finally{const m=document.getElementById('hgsmodal');if(m)m.classList.remove('open');activate('dash');}}""")
            bad = [x for x in r if x[1] != 0 or x[2] > 20]
            assert len(r) == 18 and not bad, 'stage panel rows misaligned / hint wrapped (width, offset, hint height): ' + str(bad)
        case('stages panel: rows aligned, hint on one line at 420–560 px', t_stpanel_layout)

        # ---- Dependency arrows on the hierarchy Gantt: several predecessors, rollup to visible ancestors, conflicts, editing ----
        def t_hglinks():
            r = page.evaluate("""async()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             const keep=JSON.stringify(ST.tasks),T=()=>ST.tasks,g=id=>ST.tasks.find(x=>x.id===id),tick=()=>new Promise(r=>setTimeout(r,60));
             const lns=()=>[...document.querySelectorAll('#hg_root .hg-ln')].map(x=>x.dataset.ln+(x.classList.contains('der')?':der':'')+(x.classList.contains('conf')?':conf':'')+(x.classList.contains('crit')?':crit':''));
             try{setPerm('editor');applyPerms();HG.level=9;HG.open={};HG.links=true;views();activate('hgantt');await tick();
              const demoBranch=['T-02','T-13'].map(id=>g(id).parent).join(',');
              const all=lns(),bad=document.querySelector('#hg_root .hg-linkbad').textContent;
              g('T-09').dep='T-12';hgRefresh();await tick();const conf=lns().includes('T-12>T-09:conf');
              const confList=depConflictList().some(x=>x.startsWith('T-09'));
              HG.level=2;HG.open={};hgRefresh();await tick();const l2=lns();
              HG.level=9;hgRefresh();await tick();
              // ветка иерархии: связь родитель/потомок не рисуется, показывается предупреждение
              g('T-08').dep='T-11';hgRefresh();await tick();const branch=document.querySelector('#hg_root .hg-linkbad').textContent;g('T-08').dep='';
              // панель: добавить предшественника, отказ на цикл и на ветку
              hgRefresh();await tick();document.querySelector('#hg_root [data-hgrow="T-12"] .hg-tt').click();const m=document.getElementById('hgsmodal'),ad=m.querySelector('[data-hgsadd]');
              ad.value='T-11';ad.dispatchEvent(new Event('change'));ad.value='T-11';ad.dispatchEvent(new Event('change'));
              const chips=[...m.querySelectorAll('[data-hgdeps] .depc')].length;m.querySelector('[data-hgsx=ok]').click();const panelDep=g('T-12').dep;
              const cyc=depCheck(g('T-01'),'T-13'),br=depCheck(g('T-03'),'FE-2'),self=depCheck(g('T-03'),'T-03');
              // клик по стрелке → «Удалить связь»
              hgRefresh();await tick();const gl=document.querySelector('#hg_root .hg-ln[data-ln="T-11>T-12"] .hit');
              gl.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:300,clientY:300}));const tip=!!document.querySelector('#hg_root .hg-ltip [data-hgdel="T-12"]');
              document.querySelector('#hg_root .hg-ltip [data-hgdel="T-12"]').click();const removed=g('T-12').dep;
              // «Бэклог»: несколько предшественников
              activate('backlog');const ri=ST.tasks.indexOf(g('T-20')),sel=document.querySelector('#v_backlog [data-depadd][data-di="'+ri+'"]');
              sel.value='T-16';sel.dispatchEvent(new Event('change',{bubbles:true}));const s2=document.querySelector('#v_backlog [data-depadd][data-di="'+ri+'"]');s2.value='T-17';s2.dispatchEvent(new Event('change',{bubbles:true}));
              const multi=g('T-20').dep;document.querySelector('#v_backlog [data-depdel="T-16"][data-di="'+ri+'"]').click();const afterDel=g('T-20').dep;
              const crit=cpm(ST.tasks),norm=migrate({tasks:[{id:'A',dep:''},{id:'B',dep:'A; X-9, A,B'}]}).tasks[1].dep;
              activate('hgantt');await tick();const xd=!!document.querySelector('#hg_root [data-hgrow="T-03"] .hg-xd');
              const leg0=document.querySelectorAll('#hg_root .hg-lleg > span').length;document.querySelector('#hg_root [data-hgl]').click();await tick();const off=!document.querySelector('#hg_root svg.hg-links');HG.links=true;
              const leg=leg0;
              return {demoBranch,all,bad,conf,confList,l2,branch,chips,panelDep,cyc,br,self,tip,removed,multi,afterDel,critN:crit.size,norm,xd,off,leg,errs};
             }catch(e){return 'ERR:'+e.message+' '+e.stack;}finally{window.removeEventListener('error',h);ST.tasks=JSON.parse(keep);save();HG.level=2;HG.open={};HG.links=true;views();activate('dash');}}""")
            assert isinstance(r, dict), 'hglinks failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['demoBranch'] == 'FE-1,FE-2' and r['bad'] == '', 'demo links are not inside one branch: ' + str(r)
            assert 'T-01>T-03:crit' in r['all'] and 'T-13>T-14:crit' in r['all'] and len(r['all']) == 7, 'arrows for every demo link, critical path accented: ' + str(r['all'])
            assert r['conf'] and r['confList'], 'conflicting link drawn red and listed'
            assert 'FE-1>FE-2:der' in r['l2'] and 'FE-3>FE-4:der' in r['l2'], 'collapsed: links rolled up to visible features: ' + str(r['l2'])
            assert 'одной ветки' in r['branch'], 'link inside one branch is reported'
            assert r['chips'] == 1 and r['panelDep'] == 'T-11', 'panel adds a predecessor once: ' + str(r)
            assert 'цикл' in r['cyc'] and 'ветке' in r['br'] and 'самого себя' in r['self'], 'checks: cycle, branch, self: ' + str(r)
            assert r['tip'] and r['removed'] == '', 'arrow click → remove link'
            assert r['multi'] == 'T-16, T-17' and r['afterDel'] == 'T-17', 'backlog: several predecessors: ' + str(r)
            assert r['critN'] > 0 and r['norm'] == 'A', 'critical path with lists; migrate normalises the list: ' + str(r['norm'])
            assert r['xd'] and r['off'] and r['leg'] >= 5, 'external dependency marker, links toggle, legend: ' + str(r)
        case('hglinks: dependency arrows — several predecessors, rollup, conflicts, branch/cycle checks, editing', t_hglinks)

        # ---- Hierarchy Gantt: scale/scroll, milestones, filters, columns, drag, baseline, forecast, load, export ----
        def t_hgplus():
            r = page.evaluate("""async()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             const keepT=JSON.stringify(ST.tasks),keepC=window.confirm,keepJ=window.jspdf,tick=(n)=>new Promise(r=>setTimeout(r,n||60)),g=id=>ST.tasks.find(x=>x.id===id);
             const rows=()=>[...document.querySelectorAll('#hg_root .hg-row[data-hgrow]')].map(x=>x.dataset.hgrow);
             try{setPerm('editor');applyPerms();window.confirm=()=>true;Object.assign(HG,{level:9,open:{},scale:'fit',cols:[],f:{},critOnly:false,ms:true,base:true,fc:true,load:true,marks:false,links:true});views();activate('hgantt');await tick();
              // масштаб и прокрутка
              const fitPx=document.querySelector('#hg_root .hg-grid').classList.contains('hg-px');
              const sc=document.querySelector('#hg_root [data-hgsc]');sc.value='week';sc.dispatchEvent(new Event('change',{bubbles:true}));await tick();
              const grid=document.querySelector('#hg_root .hg-grid'),scr=document.querySelector('#hg_root .hg-scroll'),wide=grid.classList.contains('hg-px')&&grid.scrollWidth>scr.clientWidth;
              document.querySelector('#hg_root [data-hgtoday]').click();const scrolled=scr.scrollLeft>0,sticky=getComputedStyle(document.querySelector('#hg_root .hg-row[data-hgrow] .hg-l')).position;
              const weekTicks=document.querySelectorAll('#hg_root .hg-head .hg-tick').length;
              const sc2=document.querySelector('#hg_root [data-hgsc]');sc2.value='quarter';sc2.dispatchEvent(new Event('change',{bubbles:true}));await tick();const q=[...document.querySelectorAll('#hg_root .hg-head .hg-tick')].map(x=>x.textContent).join('|');
              HG.scale='fit';lsSetS('hg_scale','fit');hgRefresh();await tick();
              // вехи и релизы
              const ms=[...document.querySelectorAll('#hg_root .hg-msf')].map(x=>x.textContent).join(' | '),msl=document.querySelectorAll('#hg_root .hg-row[data-hgrow] .hg-msl').length>0;
              // фильтры и поиск
              HG.f.q='оплат';hgRefresh();await tick();const qRows=rows(),found=(document.querySelector('#hg_root .hg-found')||{}).textContent||'';
              HG.f={role:'QA'};hgRefresh();await tick();const qa=rows().filter(id=>g(id)&&g(id).role==='QA'),qaAll=ST.tasks.filter(x=>x.role==='QA').every(x=>rows().includes(x.id));
              HG.f={};HG.critOnly=true;hgRefresh();await tick();const crit=cpm(ST.tasks),critOk=[...crit].every(id=>rows().includes(id));HG.critOnly=false;
              document.querySelector('#hg_root [data-hgfx]').click();await tick();const reset=rows().length===ST.tasks.length;
              // колонки
              const cb=document.querySelector('#hg_root [data-hgcol="slack"]');cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));await tick();
              const slackCell=(document.querySelector('#hg_root [data-hgrow="T-01"] .hg-c')||{}).textContent,colStored=lsGetS('hg_cols','');HG.cols=[];lsSetS('hg_cols','');hgRefresh();await tick();
              // базовый план и перетаскивание
              hgBaseFix(false);const base=JSON.stringify(g('T-12').baseline);
              const bar=document.querySelector('#hg_root .hg-p[data-hgdrag="T-12"]'),rb=bar.getBoundingClientRect(),tl=bar.closest('.hg-tl').getBoundingClientRect(),spn=bar.closest('.hg-grid').dataset.span.split(':').map(Number),ppd=tl.width/((spn[1]-spn[0])/864e5);
              const o={bubbles:true,clientX:rb.left+4,clientY:rb.top+4,pointerId:1,button:0};bar.dispatchEvent(new PointerEvent('pointerdown',o));
              document.dispatchEvent(new PointerEvent('pointermove',{...o,clientX:rb.left+4+ppd*14}));const tip=(document.querySelector('#hg_root .hg-dtip')||{}).textContent||'';
              document.dispatchEvent(new PointerEvent('pointerup',{...o,clientX:rb.left+4+ppd*14}));await tick();const moved=g('T-12').sprint;
              const shift=(document.querySelector('#hg_root [data-hgrow="T-12"] .hg-shift')||{}).textContent,bl=!!document.querySelector('#hg_root [data-hgrow="T-12"] .hg-bl');
              const kpiShift=[...document.querySelectorAll('#hg_root .hg-kpi')].map(k=>k.textContent).find(s=>s.includes('сдвиг сроков'))||'';
              const undo=document.getElementById('toastact');if(undo)undo.click();await tick();const undone=g('T-12').sprint;
              // прогноз и загрузка
              const fc=hgTree().nodes.find(x=>x.t.id==='E-1').fc,fcBar=!!document.querySelector('#hg_root [data-hgrow="E-1"] .hg-fc')||!!fc;
              const lb=document.querySelectorAll('#hg_root .hg-loadrow .hg-lb').length;
              // экспорт
              const xl=await hgExport('xlsx',true),png=await hgExport('png',true),sheet=hgSheet();
              window.jspdf={jsPDF:function(o){this.o=o;this.addImage=()=>{};this.output=()=>new Blob(['%PDF'],{type:'application/pdf'});}};const pdf=await hgExport('pdf',true);
              return {fitPx,wide,scrolled,sticky,weekTicks,q,ms,msl,qRows,found,qa:qa.length,qaAll,critOk,critN:crit.size,reset,slackCell,colStored,base,tip,moved,shift,bl,kpiShift,undone,fc:!!fc,fcBar,lb,
               xl:xl&&xl.size,png:png&&png.type,sheetRows:sheet.aoa.length,sheetCols:sheet.aoa[0].length,pdf:pdf&&pdf.type,errs};
             }catch(e){return 'ERR:'+e.message+' '+e.stack;}finally{window.removeEventListener('error',h);window.confirm=keepC;window.jspdf=keepJ;ST.tasks=JSON.parse(keepT);save();
              Object.assign(HG,{level:2,open:{},scale:'fit',cols:[],f:{},critOnly:false,load:false,marks:true});lsSetS('hg_scale','fit');views();activate('dash');}}""")
            assert isinstance(r, dict), 'hgplus failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert not r['fitPx'] and r['wide'] and r['scrolled'] and r['sticky'] == 'sticky' and r['weekTicks'] > 8, 'scale: px timeline, scroll to today, sticky labels: ' + str(r)
            assert 'Q4 2026' in r['q'], 'quarter ticks: ' + r['q']
            assert 'R-1' in r['ms'] and 'Старт проекта' in r['ms'] and r['msl'], 'milestones and releases on the scale: ' + r['ms']
            assert {'T-13', 'FE-2', 'E-1'} <= set(r['qRows']) and 'T-02' not in r['qRows'] and 'Найдено' in r['found'], 'search keeps ancestors: ' + str(r['qRows'])
            assert r['qa'] >= 2 and r['qaAll'] and r['critOk'] and r['critN'] > 0 and r['reset'], 'filters by role / critical path / reset: ' + str(r)
            assert 'спр.' in (r['slackCell'] or '') and r['colStored'] == 'slack', 'slack column: ' + str(r['slackCell'])
            assert '"a":"2026-08-17"' in r['base'], 'baseline fixed: ' + r['base']
            assert 'Спринт 3' in r['tip'] and r['moved'] == 3 and r['shift'] == '+1 спр.' and r['bl'] and '1' in r['kpiShift'], 'drag to next sprint, baseline shift: ' + str(r)
            assert r['undone'] == 2, 'undo returns the sprint'
            assert r['fc'] and r['fcBar'] and r['lb'] >= 5, 'forecast for epics, load row: ' + str(r)
            assert r['xl'] > 0 and r['png'] == 'image/png' and r['pdf'] == 'application/pdf', 'exports: ' + str(r)
            assert r['sheetCols'] == 33, 'Excel sheet columns (21 + 12 stage marks): ' + str(r['sheetCols'])
        case('hgplus: scale/scroll, milestones, filters, columns, drag, baseline, forecast, load, export', t_hgplus)

        # ---- Hierarchy Gantt, light UI: view modes, KPI chips as filters, focus, density, legend by layers, PPTX by epics ----
        def t_hglight():
            r = page.evaluate("""async()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);const tick=n=>new Promise(r=>setTimeout(r,n||60));
             const rows=()=>[...document.querySelectorAll('#hg_root .hg-row[data-hgrow]')].map(x=>x.dataset.hgrow);
             try{setPerm('editor');applyPerms();Object.assign(HG,{level:9,open:{},scale:'fit',cols:[],f:{},critOnly:false,focus:null,only:null,dense:false});views();activate('hgantt');await tick();
              const q=s=>document.querySelector('#hg_root '+s);
              q('[data-hgmode="control"]').click();await tick();const ctl={fact:HG.fact,base:HG.base,fc:HG.fc,links:HG.links,marks:HG.marks,stored:lsGetS('hg_mode','')};
              q('[data-hgmode="overview"]').click();await tick();const ov={level:HG.level,links:HG.links,marks:HG.marks,fact:HG.fact};
              const cb=q('[data-hgl]');cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));await tick();const custom=HG.mode==='custom'&&/Свой вид/.test(q('.hg-dd summary.on')?q('.hg-dd summary.on').textContent:'');
              const lleg=!!q('.hg-legp .hg-lleg'),mleg=!!q('.hg-legp .hg-mleg');
              HG.level=9;hgRefresh();await tick();q('[data-hgkf="over"]').click();await tick();const overRows=rows(),overOn=HG.f.over===true;
              q('[data-hgkf="over"]').click();await tick();const overOff=!HG.f.over&&rows().length===ST.tasks.length;
              q('.hg-row[data-hgrow="T-14"] .hg-tl').dispatchEvent(new MouseEvent('click',{bubbles:true}));await tick();
              const dim=document.querySelectorAll('#hg_root .hg-row.hg-dim').length,chip=!!q('[data-hgfocusx]'),focusRow=!!q('.hg-row.hg-focus[data-hgrow="T-14"]'),focusLinks=[...document.querySelectorAll('#hg_root .hg-ln')].map(x=>x.dataset.ln);
              document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));await tick();const esc=!HG.focus&&!document.querySelector('#hg_root .hg-dim');
              const dn=q('[data-hgdense]');dn.checked=true;dn.dispatchEvent(new Event('change',{bubbles:true}));await tick();const dense=!!q('.hg-grid.hg-dense')&&lsGetS('hg_dense','')==='1';
              const dn2=q('[data-hgdense]');dn2.checked=false;dn2.dispatchEvent(new Event('change',{bubbles:true}));await tick();
              const mini=document.querySelectorAll('#hg_root .hg-mini i').length,kpis=document.querySelectorAll('#hg_root .hg-kpi').length,cards=document.querySelectorAll('#hg_root .kpi').length;
              let pp=null;try{await loadPptxGen();const res=await hgExportPptx(true);pp={n:res.n,b64:await res.p.write('base64'),epics:hgTree().nodes.filter(x=>x.ch.length).length};}catch(e){pp={err:String(e.message||e)};}
              const restored=HG.only===null&&HG.level===9;
              return {ctl,ov,custom,lleg,mleg,overRows,overOn,overOff,dim,chip,focusRow,focusLinks,esc,dense,mini,kpis,cards,pp,restored,errs};}
             catch(e){return 'ERR:'+e.message+' '+e.stack;}finally{window.removeEventListener('error',h);HG.mode='overview';lsSetS('hg_mode','overview');Object.assign(HG,HG_MODES.overview,{level:2,open:{},f:{},focus:null,only:null,dense:false});lsSetS('hg_dense','0');views();activate('dash');}}""")
            assert isinstance(r, dict), 'hglight failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['ctl'] == {'fact': True, 'base': True, 'fc': True, 'links': False, 'marks': False, 'stored': 'control'}, 'mode «Контроль»: ' + str(r['ctl'])
            assert r['ov'] == {'level': 2, 'links': False, 'marks': False, 'fact': False}, 'mode «Обзор»: ' + str(r['ov'])
            assert r['custom'] and r['lleg'] and not r['mleg'], 'manual layer → «Свой вид», legend shows only active layers: ' + str(r)
            assert r['overOn'] and 'T-12' in r['overRows'] and 'T-02' not in r['overRows'] and r['overOff'], 'KPI chip toggles the overdue filter: ' + str(r['overRows'])
            assert r['dim'] > 0 and r['chip'] and r['focusRow'] and set(r['focusLinks']) == {'T-01>T-03', 'T-03>T-13', 'T-13>T-14'} and r['esc'], 'focus on the T-14 chain, Esc clears: ' + str(r)
            assert r['dense'], 'compact rows'
            assert r['mini'] >= 20 and r['kpis'] >= 4 and r['cards'] == 0, 'progress mini bars, KPI chips instead of cards: ' + str(r)
            assert r['restored'], 'export restores the view state'
            pp = r['pp']
            if pp.get('err'):
                print('    (PPTX skipped: ' + pp['err'] + ')')
            else:
                z = zipfile.ZipFile(io.BytesIO(base64.b64decode(pp['b64'])))
                slides = [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)]
                assert pp['n'] == 3 + pp['epics'] and len(slides) == pp['n'], 'PPTX by epics: title + overview + epics + summary: ' + str((pp['n'], len(slides)))
                txt = ''.join(z.read(n).decode('utf-8', 'ignore') for n in slides)
                assert 'Что требует внимания' in txt and 'Обзор: эпики и фичи' in txt, 'PPTX slide titles'
        case('hglight: view modes, KPI chips, focus, density, legend by layers, PPTX by epics', t_hglight)

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

        # ---- 30. Team health & performance package (v1.43) ----
        def t_health_perf():
            r = page.evaluate("""()=>{try{
              // bus factor from Star Map
              const B=busFactor();
              // DORA from deployments + incidents
              const D=dora();
              const tiers=['Elite','High','Medium','Low','—'];
              const dOk=[D.tFreq,D.tLead,D.tCfr,D.tMttr].every(t=>tiers.includes(t));
              const cfrOk=D.count?Math.abs(D.cfr - D.failed/D.count)<1e-9:D.cfr===0;
              // aging WIP + say-do
              const aw=agingWip(); const agingOk=aw.every(x=>x.age>=0) && (aw.length<2 || aw[0].age>=aw[1].age);
              const sd=sayDo(compute()); const sdOk=sd.avg===null||(sd.avg>=0);
              // health check latest-per-dimension
              const hc=hcLatest(); const hcDims=Object.keys(hc).length;
              // seeded registers
              const seeded=['teamHealth','deployments','incidents'].every(k=>Array.isArray(ST[k])&&ST[k].length>0);
              return {busShape:('bf'in B&&'spof'in B&&'uncovered'in B), dOk, cfrOk, agingOk, sdOk, hcDims, seeded};
            }catch(e){return 'ERR:'+e.message;}}""")
            assert r is not True and isinstance(r, dict), 'health/perf failed: ' + str(r)
            assert r['busShape'], 'busFactor() shape invalid'
            assert r['dOk'] and r['cfrOk'], 'DORA tiers/CFR invalid'
            assert r['agingOk'], 'aging WIP ordering/age invalid'
            assert r['sdOk'], 'say-do ratio invalid'
            assert r['hcDims'] >= 1 and r['seeded'], 'health check / registers not seeded'
        case('health-perf: bus factor, DORA, aging WIP, say-do, health check', t_health_perf)

        # ---- 31. NAV integrity: unique ids, every id has a container ----
        def t_nav():
            r = page.evaluate("""()=>{const ids=NAV.flatMap(g=>g.items.map(i=>i[0]));
              const dups=ids.filter((x,i)=>ids.indexOf(x)!==i);
              const missing=ids.filter(id=>!document.getElementById('v_'+id));
              return {n:ids.length, uniq:new Set(ids).size, dups, missing, groups:NAV.length,
                      names:NAV.map(g=>g.g)};}""")
            assert r['n'] == r['uniq'], 'duplicate NAV ids: ' + str(r['dups'])
            assert not r['missing'], 'NAV ids without a v_ container: ' + str(r['missing'])
            assert r['groups'] >= 8, 'unexpectedly few nav groups'
            assert 'Обзор' in r['names'] and 'Команда' in r['names'], 'expected regrouped blocks missing'
        case('nav: unique ids, containers, regrouped blocks', t_nav)

        # ---- 39. Ergonomics: lazy views, compact nav (hubs, tabs, search), compact header, quick create ----
        def t_ergonomics():
            r = page.evaluate("""async()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             try{setPerm('admin');applyPerms();NAVS.mode='compact';activate('dash');views();
              const lazyBefore=document.querySelectorAll('#v_backlog .lazy-ph').length;activate('backlog');const lazyAfter=document.querySelectorAll('#v_backlog .lazy-ph').length;
              const allTitles=NAV.flatMap(g=>g.items.map(i=>i[0])).every(id=>{const v=document.getElementById('v_'+id);return v&&v.querySelector('h1');});
              const navIds=NAV.flatMap(g=>g.items.map(i=>i[0])),mapped=new Set(NAV2.flatMap(e=>e[3]));
              const covered=navIds.every(id=>mapped.has(id)),noMore=!NAV2.some(e=>e[0]==='h_more');
              activate('wsjf');const tabs=[...document.querySelectorAll('#v_wsjf > .hub-tabs [data-hubv]')].map(b=>b.dataset.hubv);
              document.querySelector('#v_wsjf > .hub-tabs [data-hubv=moscow]').click();const tabGo=CURV==='moscow';
              const hubTarget=document.querySelector('#nav .nav-hubs .nav-item[data-v=moscow]')!==null;
              const entries=document.querySelectorAll('#nav .nav-hubs:not(.nav-smart) .nav-item').length,lvl=!!document.querySelector('#nav [data-lvl]');
              navFilter('гант');const found=[...document.querySelectorAll('#nav .nav-allg .nav-row')].filter(x=>x.style.display!=='none').map(x=>x.querySelector('.nav-lbl').textContent);navFilter('');
              document.querySelector('#nav [data-navmode=all]').click();const allMode=NAVS.mode==='all'&&!document.getElementById('nav').classList.contains('nav2')&&!document.querySelector('#v_moscow > .hub-tabs');
              document.querySelector('#nav [data-navmode=compact]').click();const back=NAVS.mode==='compact'&&!!document.querySelector('#v_moscow > .hub-tabs');
              activate('dash');
              const n0=ST.tasks.length;await qcOpen('task');const m=document.getElementById('qcmodal');m.querySelector('[data-q=title]').value='Быстрая задача';qcSubmit(QC[0]);
              const last=ST.tasks[ST.tasks.length-1];const qcOk=ST.tasks.length===n0+1&&last.title==='Быстрая задача'&&+last.sprint===compute().cur;
              ST.tasks.pop();save();views();activate('dash');
              const qcItems=(qcRender(),[...document.querySelectorAll('#qcpop [data-qc]')].map(b=>b.dataset.qc)),qcWiz=!!document.querySelector('#qcpop [data-proj]');
              setPerm('viewer');applyPerms();qcRender();const qcWizViewer=!!document.querySelector('#qcpop [data-proj]');setPerm('admin');applyPerms();
              const dense0=document.body.classList.contains('dense');document.getElementById('densbtn').click();const dense1=document.body.classList.contains('dense');document.getElementById('densbtn').click();
              const lede=document.querySelector('#v_dash > .lede'),clamp=getComputedStyle(lede).webkitLineClamp;
              const loadKpi=[...document.querySelectorAll('#v_dash .kpi')].map(k=>k.textContent).find(s=>s.includes('Загрузка'))||'';
              return {lazyBefore,lazyAfter,allTitles,covered,noMore,tabs,tabGo,hubTarget,entries,lvl,found,allMode,back,qcOk,qcItems,qcWiz,qcWizViewer,
                dense:!dense0&&dense1&&!document.body.classList.contains('dense'),clamp,nan:loadKpi.includes('NaN'),errs};
             }catch(e){return 'ERR:'+e.message;}finally{window.removeEventListener('error',h);}}""")
            assert isinstance(r, dict), 'ergonomics failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['lazyBefore'] > 0 and r['lazyAfter'] == 0, 'hidden sections must build on open: ' + str(r)
            assert r['allTitles'], 'every section keeps its title (assistant/search) without being built'
            assert r['covered'] and r['noMore'], 'every NAV section must be mapped to a hub (no «Ещё»)'
            assert r['tabs'] == ['rice', 'wsjf', 'moscow'] and r['tabGo'] and r['hubTarget'], 'hub tabs and last tab memory: ' + str(r)
            assert 12 <= r['entries'] <= 18 and not r['lvl'], 'compact menu: 12-18 entries, no level switch, got ' + str(r)
            assert r['found'] == ['Гант', 'Гант по иерархии'], 'search must find sections inside hubs: ' + str(r['found'])
            assert r['allMode'] and r['back'], '«Все разделы» toggles the full menu and back: ' + str(r)
            assert r['qcOk'], 'quick create must add a task to the current sprint'
            assert r['qcItems'] == ['task', 'bug', 'risk', 'imp'] and r['qcWiz'] and not r['qcWizViewer'], 'quick create menu: ' + str(r)
            assert r['dense'], 'density toggle'
            assert r['clamp'] == '1', 'section description is one line'
            assert not r['nan'], 'load KPI must not show NaN'
        case('ergonomics: lazy views, compact nav hubs/tabs/search, header, quick create, density', t_ergonomics)

        # ---- 40. Scenarios: «Мой день», first steps for an empty project, «Новый проект» wizard ----
        def t_scenarios():
            r = page.evaluate("""async()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             const keep=JSON.stringify(ST);
             try{setPerm('admin');applyPerms();
              const me=ST.team[0].name;lsSetS('me',me);views();activate('myday');
              const cur=compute().cur,mine=ST.tasks.filter(t=>+t.sprint===cur&&t.assignee===me&&t.type!=='Эпик');
              const rows=document.querySelectorAll('#myday_root .md-task').length;
              const todo=mine.find(t=>t.status==='To Do');let started=true;
              if(todo){const st0=todo.status;document.querySelector('#myday_root [data-md=start][data-id="'+todo.id+'"]').click();started=ST.tasks.find(t=>t.id===todo.id).status==='В работе';ST.tasks.find(t=>t.id===todo.id).status=st0;save();}
              lsSetS('me','');views();activate('myday');const allRows=document.querySelectorAll('#myday_root .md-task').length;
              const allSp=ST.tasks.filter(t=>+t.sprint===cur&&t.type!=='Эпик').length;
              const cards=document.querySelectorAll('#myday_root .md-grid > .card').length,onbDemo=!!document.querySelector('#myday_root .onb');
              projOpen();const m=document.getElementById('projmodal');const set=(k,v)=>{m.querySelector('[data-w='+k+']').value=v;};
              set('name','Мобильное приложение');set('goal','Выпустить MVP');set('start','2026-11-02');set('days','10');set('sprints','8');
              set('team',['Орлова Е. — Frontend','Белов И. — qa','Новиков П.'].join(String.fromCharCode(10)));
              set('tasks',['Прототип главного экрана','Авторизация'].join(String.fromCharCode(10)));
              m.querySelector('[data-w=backup]').checked=false;projRun();
              const P=ST.params,re=load();
              const KEEP=['dod','dorItems','calendar','faq','ishikawaCats','boards','team','tasks'];
              const leftovers=Object.keys(re).filter(k=>Array.isArray(re[k])&&re[k].length&&!KEEP.includes(k));
              const wiz={name:P.name,goal:P.goal,start:P.start,sprints:P.sprints,team:ST.team.map(x=>x.name+'/'+x.role),tasks:ST.tasks.map(x=>x.id+':'+x.title+':'+x.sprint),
                epics:re.tasks.filter(t=>t.type==='Эпик').length,leftovers,board:(re.board.items||[]).length,view:CURV};
              const onb=!!document.querySelector('#myday_root .onb');activate('dash');const onbDash=!!document.querySelector('#v_dash > .onb-wrap .onb');
              const steps=onbSteps().filter(s=>s[2]).map(s=>s[0]);
              document.querySelector('#v_dash > .onb-wrap [data-onb=hide]').click();const hidden=!document.querySelector('#v_dash > .onb-wrap');lsSetS('onb_off','');
              return {mine:mine.length,rows,started,allRows,allSp,cards,onbDemo,wiz,onb,onbDash,steps,hidden,errs};
             }catch(e){return 'ERR:'+e.message;}finally{window.removeEventListener('error',h);setPerm('admin');ST=migrate(JSON.parse(keep));save();views();activate('dash');}}""")
            assert isinstance(r, dict), 'scenarios failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['rows'] == r['mine'] and r['allRows'] == r['allSp'], 'my day lists my / all tasks of the current sprint: ' + str(r)
            assert r['started'], 'start button must change the task status'
            assert r['cards'] == 3 and not r['onbDemo'], 'my day: tasks, attention, events; no first steps for demo data: ' + str(r)
            w = r['wiz']
            assert (w['name'], w['goal'], w['start'], w['sprints']) == ('Мобильное приложение', 'Выпустить MVP', '2026-11-02', 8), str(w)
            assert w['team'] == ['Орлова Е./Frontend', 'Белов И./QA', 'Новиков П./'], 'team lines «Имя — роль»: ' + str(w['team'])
            assert w['tasks'] == ['T-01:Прототип главного экрана:1', 'T-02:Авторизация:1'], str(w['tasks'])
            assert w['epics'] == 0 and w['leftovers'] == [] and w['board'] == 0, 'no demo data after reload: ' + str(w)
            assert w['view'] == 'myday', 'wizard opens «Мой день»'
            assert r['onb'] and r['onbDash'] and r['hidden'], 'new project shows first steps (my day + dashboard), hide works: ' + str(r)
            assert r['steps'] == ['params', 'team', 'backlog'], 'done steps for the new project: ' + str(r['steps'])
        case('scenarios: my day, first steps, «Новый проект» wizard', t_scenarios)

        # ---- Profile: «Мой профиль» — who am I, my work/time, mentions, settings; server binding & own password ----
        def t_profile():
            r = page.evaluate("""async()=>{const errs=[];const h=e=>errs.push(String(e.message||e.reason||e));window.addEventListener('error',h);
             const KEY=()=>%(KEY)s,keepMe=lsGetS(KEY(),''),keepFetch=window.fetch,keepAuth=Object.assign({},AUTH),keepBoard=JSON.stringify(ST.board||{});
             try{setPerm('editor');applyPerms();lsSetS(KEY(),'');views();activate('dash');
              document.getElementById('profbtn').click();const opened=CURV==='profile';
              const tabs=[...document.querySelectorAll('#v_profile > .hub-tabs [data-hubv]')].map(b=>b.dataset.hubv);
              const noMe=!!document.querySelector('#prof_root .md-empty');const me=ST.team[0].name;
              const sel=document.querySelector('#prof_root [data-pf=me]');sel.value=me;sel.dispatchEvent(new Event('change',{bubbles:true}));
              await new Promise(r=>setTimeout(r,80));
              const stored=lsGetS(KEY(),'')===me&&mdMe()===me;
              const open=ST.tasks.filter(t=>t.type!=='Эпик'&&t.assignee===me&&t.status!=='Готово').length;
              const head=[...document.querySelectorAll('#prof_root .md-h')].map(x=>x.textContent);
              const workOk=head.some(x=>x==='Моя работа — открытых задач: '+open);
              const it=(ST.board.items=ST.board.items||[]);it.push({id:'pf-test',t:'sticky',x:0,y:0,w:100,h:80,text:'Тест',comments:[{id:'c1',a:'Петрова М.',t:'@'+me+' посмотри, пожалуйста',ts:'2026-09-10T10:00:00Z',m:[me]}]});
              views();activate('profile');const ment=[...document.querySelectorAll('#prof_root .md-li[data-mdgo=board]')].some(b=>b.textContent.includes('посмотри'));
              const localPw=!document.querySelector('#prof_root [data-pw]');
              const d0=document.body.classList.contains('dense');document.querySelector('#prof_root [data-pf=dense]').click();const d1=document.body.classList.contains('dense');
              document.querySelector('#prof_root [data-pf=dense]').click();const dense=!d0&&d1&&!document.body.classList.contains('dense')&&CURV==='profile';
              // сервер: привязка в учётной записи и смена пароля (ответы сервера подменены)
              const calls=[];let pwStatus=204;
              window.fetch=(u,o)=>{const s=String(u);const J=(x,st)=>Promise.resolve(new Response(x==null?null:JSON.stringify(x),{status:st||200,headers:{'Content-Type':'application/json'}}));
               if(s.includes('api/auth/me/password')){calls.push(['pw',JSON.parse(o.body)]);return pwStatus===204?J(null,204):J({error:'wrong_password'},pwStatus);}
               if(s.includes('api/auth/me')&&o&&o.method==='PUT'){const b=JSON.parse(o.body);calls.push(['me',b]);return J({username:'po',role:'EDITOR',name:'PO',member:b.member||null});}
               return keepFetch(u,o);};
              AUTH.mode='server';AUTH.token='demo';AUTH.username='po';AUTH.user='PO';AUTH.role='EDITOR';AUTH.member='';
              const other=ST.team[1].name;await profSetMe(other);lsSetS(KEY(),me);
              const srvMe=AUTH.member===other&&mdMe()===other;views();activate('profile');
              const set=(k,v)=>{document.querySelector('#prof_root [data-pw='+k+']').value=v;};const msg=()=>document.getElementById('pf_pwmsg').textContent;
              set('old','Old-pass-1');set('new','New-pass-2');set('rep','New-pass-X');await profPassword();const mism=msg();
              set('new','short');set('rep','short');await profPassword();const shortM=msg();
              set('new','New-pass-2');set('rep','New-pass-2');await profPassword();const okM=msg();
              pwStatus=403;set('old','bad');set('new','New-pass-3');set('rep','New-pass-3');await profPassword();const badM=msg();
              uiMenuSync();const lo=document.getElementById('logoutbtn').style.display!=='none';
              return {opened,tabs,noMe,stored,workOk,head,ment,localPw,dense,srvMe,calls:calls.map(c=>c[0]),meBody:calls[0]&&calls[0][1],pwBody:(calls.find(c=>c[0]==='pw')||[])[1],mism,shortM,okM,badM,lo,errs};
             }catch(e){return 'ERR:'+e.message;}
             finally{window.removeEventListener('error',h);window.fetch=keepFetch;Object.assign(AUTH,keepAuth);ST.board=JSON.parse(keepBoard);lsSetS(KEY(),keepMe);uiMenuSync();views();activate('dash');}}""" % {'KEY': "'me'"})
            assert isinstance(r, dict), 'profile failed: ' + str(r)
            assert not r['errs'], 'page errors: ' + str(r['errs'][:3])
            assert r['opened'] and r['tabs'] == ['myday', 'profile'], 'profile opens from the user menu, tab next to «Мой день»: ' + str(r)
            assert r['noMe'] and r['stored'], 'member binding: prompt when unset, stored after choice'
            assert r['workOk'] and {'Кто я', 'Моё время', 'Настройки'} <= set(r['head']), 'profile cards: ' + str(r['head'])
            assert r['ment'], 'board @mention shows in profile'
            assert r['localPw'] and r['dense'], 'local mode: no password form; settings toggle density'
            assert r['srvMe'] and r['meBody'] == {'member': r['meBody']['member']} and r['meBody']['member'], 'server binding wins over the browser choice: ' + str(r)
            assert r['calls'].count('pw') == 2 and r['pwBody'] == {'oldPassword': 'Old-pass-1', 'newPassword': 'New-pass-2'}, 'password requests: ' + str(r)
            assert 'не совпадают' in r['mism'] and '8 символов' in r['shortM'] and 'изменён' in r['okM'] and 'неверно' in r['badM'], str(r)
            assert r['lo'], 'logout visible in the user menu with server session'
        case('profile: who am I, my work/time, mentions, settings, server binding & own password', t_profile)

        # ---- Viewer: personal controls (profile, «Я —», Gantt view) stay usable in read-only mode ----
        def t_viewer_free():
            r = page.evaluate("""()=>{const keepAuth=Object.assign({},AUTH);
             try{setPerm('viewer');applyPerms();AUTH.mode='server';AUTH.token='demo';AUTH.username='v';AUTH.user='Наблюдатель';AUTH.role='VIEWER';
              views();activate('profile');const me=document.querySelector('#prof_root [data-pf=me]'),pw=document.querySelector('#prof_root [data-pw=old]'),btn=document.querySelector('#prof_root [data-pf=pw]');
              const prof=!!me&&!me.disabled&&!!pw&&!pw.readOnly&&!!btn&&btn.offsetParent!==null;
              activate('myday');const mm=document.querySelector('#myday_root [data-md=me]');const md=!!mm&&!mm.disabled;
              activate('hgantt');const hf=document.querySelector('#hg_root [data-hgf]');const hg=!!hf&&!hf.disabled;
              activate('backlog');const data=[...document.querySelectorAll('#v_backlog td input, #v_backlog td select')].every(e=>e.disabled||e.readOnly);
              return {prof,md,hg,data};}
             finally{Object.assign(AUTH,keepAuth);setPerm('editor');applyPerms();views();activate('dash');}}""")
            assert r['prof'], 'profile: member select, password fields and button usable for VIEWER'
            assert r['md'] and r['hg'], 'my day «Я —» and Gantt fact toggle usable for VIEWER: ' + str(r)
            assert r['data'], 'project data stays read-only for VIEWER'
        case('viewer: personal controls stay usable, data read-only', t_viewer_free)

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
