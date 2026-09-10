# Планирование спринтов — полиглот-приложение

Система планирования спринтов с реальным бэкендом и базой данных **PostgreSQL**.
Переписана на два серверных языка:

- **Java (Spring Boot)** — REST API, CRUD и хранение данных в PostgreSQL (JPA/Hibernate).
- **Python (FastAPI)** — сервис аналитики и метрик (velocity, RICE, прогнозы, сгорание, зависимости),
  читает ту же базу через SQLAlchemy.
- **Веб-интерфейс** — тот же одностраничный UI (HTML/CSS/JS, все вкладки, графики, диаграмма Ганта),
  подключён к API через reverse-proxy nginx.

Всё поднимается одной командой через **docker-compose**.

## Архитектура

```
┌────────────┐     /api/*        ┌──────────────────────┐
│  Браузер   │ ───────────────▶  │  Java Spring Boot API │──┐
│ (nginx web)│                   │  (CRUD, /api/state)   │  │   JDBC
│            │     /analytics/*  ├──────────────────────┤  ├──▶ ┌────────────┐
│            │ ───────────────▶  │  Python FastAPI      │──┘     │ PostgreSQL │
└────────────┘                   │  (метрики, аналитика)│  SQLAlchemy ────────▶│
                                 └──────────────────────┘        └────────────┘
```

Единый источник схемы и стартовых данных — `db/init.sql` (применяется при первом старте PostgreSQL).

## Быстрый старт

Требуется Docker + Docker Compose.

```bash
docker compose up --build
```

Затем открыть **http://localhost:8080**.

Опционально прямой доступ к сервисам: Java API — `http://localhost:8081`, Python — `http://localhost:8000`.

Общий ключ команды (защита API): задать переменную окружения `TEAM_TOKEN` перед запуском —
тогда UI при первом входе спросит ключ.

## Сервисы и эндпоинты

**Java API (`/api`)**
| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/state` | всё состояние приложения (документ) + версия |
| PUT | `/api/state` | заменить состояние (тело `{ "state": { … } }`), версия +1 |
| HEAD | `/api/state` | проба доступности / авторизации |
| GET/POST/PUT/DELETE | `/api/tasks[/{id}]` | пример полноценного REST-ресурса поверх JPA |
| GET | `/api/health` | статус сервиса |

**Python аналитика (`/analytics`)**
| Метод | Путь | Назначение |
|---|---|---|
| GET | `/analytics/health` | статус сервиса и БД |
| GET | `/analytics/metrics` | спринты, velocity, health, TTM, DRE, прогноз, кварталы |
| GET | `/analytics/rice` | ранжирование фич по RICE |
| GET | `/analytics/burndown` | ряды сгорания (остаток / идеал / сделано) |
| GET | `/analytics/dependencies` | сводка межстримовых зависимостей |

## Структура репозитория

| Путь | Назначение |
|---|---|
| `db/init.sql` | Схема PostgreSQL + стартовые данные (источник правды) |
| `backend-java/` | Spring Boot API (Maven, JPA, PostgreSQL) |
| `analytics-python/` | FastAPI-сервис аналитики (SQLAlchemy) |
| `frontend/` | UI (`index.html`) + nginx reverse-proxy |
| `docker-compose.yml` | Оркестрация: db + api + analytics + web |
| `data/seed.json` | Исходные данные (справочно; из них сгенерирован `init.sql`) |
| `Планирование_спринта_PRO.xlsx` | Книга-первоисточник (30 листов) |
| `*_описание_*.docx` | Описание листов/метрик |

## Локальная разработка (без Docker)

1. Поднять PostgreSQL и применить `db/init.sql`.
2. Java: `cd backend-java && mvn spring-boot:run` (env `DB_URL/DB_USER/DB_PASSWORD`).
3. Python: `cd analytics-python && pip install -r requirements.txt && uvicorn app.main:app --port 8000`
   (env `DB_URL_PY`).
4. Открыть `frontend/index.html` (для REST-режима нужен reverse-proxy или CORS — проще запускать через compose).

## Модель данных и расчёты

- Каждая коллекция приложения — отдельная таблица PostgreSQL (`tasks`, `team`, `releases`, `deps`, `rice`, …).
- Java собирает/сохраняет весь документ состояния через `/api/state`, сохраняя порядок строк (`ord`).
- Даты спринта: `старт + (n−1)·14 … +11`; рабочие дни — будни минус праздники из таблицы `calendar`.
- Ёмкость спринта = Σ `(раб.дни − отсутствия) × доступность × Focus factor`.
- velocity = Σ оценок задач со статусом «Готово» (для закрытых спринтов); RICE = (Reach × Impact × Confidence) / Effort.
- Метрики считает Python-сервис (единый движок), результат сверяется с клиентским расчётом UI.

> Примечание: многопользовательский режим обеспечивается общей БД. GitHub Pages для этой версии не подходит —
> нужен запуск полного стека (docker-compose или собственный хостинг).
