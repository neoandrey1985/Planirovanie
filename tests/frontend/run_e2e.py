# -*- coding: utf-8 -*-
"""End-to-end / functional test suite for the Планирование спринтов frontend SPA.

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
