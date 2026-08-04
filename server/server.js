// Планирование спринтов — многопользовательский бэкенд.
// Общее состояние приложения в SQLite (встроенный node:sqlite, без внешних зависимостей).
// Раздаёт то же приложение (index.html) и REST API /api/state.
'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');

const ROOT = path.join(__dirname, '..');                 // корень репозитория: index.html, data/
const PORT = process.env.PORT || 3000;
const TOKEN = process.env.TEAM_TOKEN || '';              // необязательный общий ключ команды
const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data.db');

// --- база данных -----------------------------------------------------------
const db = new DatabaseSync(DB_PATH);
db.exec('CREATE TABLE IF NOT EXISTS app(id INTEGER PRIMARY KEY, version INTEGER NOT NULL, state TEXT NOT NULL, updated_at TEXT)');
if (!db.prepare('SELECT 1 FROM app WHERE id=1').get()) {
  let seed = {};
  try { seed = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'seed.json'), 'utf8')); } catch (e) {}
  db.prepare('INSERT INTO app(id,version,state,updated_at) VALUES(1,1,?,?)')
    .run(JSON.stringify(seed), new Date().toISOString());
}
const qGet = db.prepare('SELECT version,state,updated_at FROM app WHERE id=1');
const qUpd = db.prepare('UPDATE app SET version=version+1, state=?, updated_at=? WHERE id=1');

// --- статика ---------------------------------------------------------------
const MIME = {
  '.html': 'text/html; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.png': 'image/png', '.svg': 'image/svg+xml',
  '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
};

function authOk(req, url) {
  if (!TOKEN) return true;
  const t = req.headers['x-team-token'] || url.searchParams.get('token');
  return t === TOKEN;
}
function sendJson(res, code, obj) {
  const b = Buffer.from(JSON.stringify(obj));
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': b.length, 'Cache-Control': 'no-store' });
  res.end(b);
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = url.pathname;

  // ---- API: общее состояние ----
  if (p === '/api/state') {
    if (!authOk(req, url)) return sendJson(res, 401, { error: 'unauthorized' });
    if (req.method === 'HEAD') { res.writeHead(200); return res.end(); }
    if (req.method === 'GET') {
      const r = qGet.get();
      return sendJson(res, 200, { version: r.version, state: JSON.parse(r.state), updatedAt: r.updated_at });
    }
    if (req.method === 'PUT') {
      let body = '';
      req.on('data', c => { body += c; if (body.length > 8e6) req.destroy(); });
      req.on('end', () => {
        try {
          const j = JSON.parse(body);
          if (j.state == null) return sendJson(res, 400, { error: 'state required' });
          const now = new Date().toISOString();
          qUpd.run(JSON.stringify(j.state), now);
          const r = qGet.get();
          sendJson(res, 200, { version: r.version, updatedAt: now });
        } catch (e) { sendJson(res, 400, { error: 'bad json' }); }
      });
      return;
    }
    res.writeHead(405); return res.end();
  }

  // ---- статические файлы приложения ----
  let rel = decodeURIComponent(p);
  if (rel === '/' || rel === '') rel = '/index.html';
  const fp = path.normalize(path.join(ROOT, rel));
  if (!fp.startsWith(ROOT)) { res.writeHead(403); return res.end('Forbidden'); }
  fs.readFile(fp, (err, data) => {
    if (err) { // не найдено — отдаём приложение (SPA-навигация)
      fs.readFile(path.join(ROOT, 'index.html'), (e2, d2) => {
        if (e2) { res.writeHead(404); res.end('Not found'); }
        else { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(d2); }
      });
      return;
    }
    const ext = path.extname(fp).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log('Планирование спринтов — сервер на порту ' + PORT + (TOKEN ? ' [защита ключом]' : ' [открытый доступ]'));
  console.log('База данных: ' + DB_PATH);
});
