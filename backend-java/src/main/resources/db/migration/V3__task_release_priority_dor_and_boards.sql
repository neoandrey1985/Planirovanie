-- v1.25: явная привязка задач к релизу, приоритет, готовность (DoR) и определения Kanban-досок.

-- Новые поля задачи (клиентские поля, ранее не сохранявшиеся на сервере).
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS release_id TEXT;  -- ссылка на releases.rel_id (мягкая связь)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority   TEXT;  -- приоритет (MoSCoW-категория или RICE-балл)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS dor        TEXT;  -- Definition of Ready ('' | 'Готова')

-- Определения Kanban-досок (коллекция boards клиентского состояния).
CREATE TABLE IF NOT EXISTS boards (
  pk           SERIAL PRIMARY KEY,
  board_id     TEXT,        -- бизнес-ID доски (b-all, b-backend, …)
  name         TEXT,        -- отображаемое имя вкладки
  filter_type  TEXT,        -- all | role | release | release-compose
  filter_value TEXT,        -- имя роли для досок по ролям (иначе NULL)
  cols         TEXT,        -- JSON-массив колонок-статусов
  ord          INT          -- порядок вкладок
);
