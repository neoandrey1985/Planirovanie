# Управление кросс-функциональной командой — agent & contributor guide

Веб-приложение для agile-планирования по двухнедельным спринтам. Полиглот-стек:
`frontend/` (самодостаточный SPA на ванильном JS в одном `index.html`),
`backend-java/` (Spring Boot REST API + PostgreSQL, Flyway-миграции),
`analytics-python/` (FastAPI — движок метрик), `nginx` (reverse-proxy),
всё поднимается через `docker-compose.yml`.

## Build / run

```bash
make up            # собрать и запустить весь стек на http://localhost:8080
make build         # только собрать образы
docker compose down
```

Локальный предпросмотр только фронтенда: `python -m http.server 4180 --directory frontend`.

## Test — регрессия по всему функционалу

Один прогон покрывает всё приложение. **Запускай перед каждым коммитом; CI гоняет то же на каждый push/PR.**

```bash
make test            # Java (Spring Boot + H2) + Python + frontend e2e — полная регрессия
make test-java       # backend:  cd backend-java && mvn -B -ntp test   (MockMvc, H2)
make test-python     # analytics: python analytics-python/tests/test_compute.py
make test-frontend   # frontend:  python tests/frontend/run_e2e.py     (Playwright, всё приложение)
```

- **Frontend e2e** — [`tests/frontend/run_e2e.py`](tests/frontend/run_e2e.py): поднимает статический сервер,
  запускает headless Chromium, проверяет метрики, EDA, экспорт Excel/PPTX (в т.ч. регресс на «битый файл»),
  Kanban, релизы, доску, миграции и права. См. [`tests/frontend/README.md`](tests/frontend/README.md).
- **Backend** запускается в песочнице только через `mvn -o test` (MockMvc); живой Tomcat/RANDOM_PORT в песочнице
  не стартует — не полагайся на него в тестах.

## Правило: новый функционал → автотесты (обязательно)

Любой PR, добавляющий или меняющий поведение, обязан обновить тесты в том же изменении:

1. **Новый раздел приложения** (пункт в `NAV` в `frontend/index.html`) покрывается **автоматически** —
   smoke-цикл в `run_e2e.py` сам обнаруживает все разделы из `NAV` и проверяет, что каждый рендерится без
   ошибок консоли. Отдельный код теста писать не нужно.
2. **Новая логика** (расчётный путь, экспорт, автоматизация, новая модель данных, серверный эндпоинт) требует
   **отдельного теста**:
   - фронтенд — добавь блок `case('<область>: <поведение>', t_fn)` в `run_e2e.py` по образцу соседних;
     проверяй форму данных и диапазоны, а не точные значения демо-данных, чтобы тест не «краснел» при смене seed;
   - backend — добавь тест в `backend-java/src/test/...` (MockMvc);
   - analytics — расширь `analytics-python/tests/`.
3. Прогони `make test`. Красный тест — блокер, чинится причина, а не тест.

Регрессия по определению покрывает весь функционал: `make test` — это и есть регрессионный набор.

## Code style / соглашения

- Фронтенд — единый `frontend/index.html` (без сборки): правь его напрямую. Разделы = группы в `NAV`,
  контейнеры `#v_<id>`, рендер через `views()`/`setView()`; вся запись данных проходит через `save()`
  (гейт `PERM.canEdit`). Версия — `APP_VERSION`, история — `CHANGELOG` (голова changelog обязана совпадать с версией; это проверяет тест).
- После изменения приложения обновляй сопутствующие документы (руководства, презентация, инструкция по
  развёртыванию) и перезаписывай скриншоты, затем пушь в GitHub.
- Ветка по умолчанию — `main`; CI обязателен к прохождению до merge.
