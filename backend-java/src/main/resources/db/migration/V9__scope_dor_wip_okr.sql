-- v1.40: task carryover counter + OKR link, Kanban WIP limits,
-- Definition of Ready checklist, scope-creep log.

ALTER TABLE tasks  ADD COLUMN IF NOT EXISTS carried INTEGER;
ALTER TABLE tasks  ADD COLUMN IF NOT EXISTS okr TEXT;
ALTER TABLE boards ADD COLUMN IF NOT EXISTS wip TEXT;

CREATE TABLE IF NOT EXISTS dor_items (
    id   BIGSERIAL PRIMARY KEY,
    crit TEXT,
    done BOOLEAN,
    ord  INTEGER
);

CREATE TABLE IF NOT EXISTS scope_log (
    pk         BIGSERIAL PRIMARY KEY,
    sc_id      TEXT,
    date       TEXT,
    sprint     INTEGER,
    release_id TEXT,
    kind       TEXT,
    item       TEXT,
    detail     TEXT,
    ord        INTEGER
);
