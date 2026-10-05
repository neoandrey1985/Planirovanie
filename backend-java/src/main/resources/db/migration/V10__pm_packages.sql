-- v1.42: full PM packages — change control, issues, stakeholders, decisions,
-- impediments, lessons, RACI, story map, planning poker, portfolio; WBS parent on tasks.

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS parent TEXT;

CREATE TABLE IF NOT EXISTS change_requests (
    pk BIGSERIAL PRIMARY KEY, cr_id TEXT, date TEXT, title TEXT, type TEXT,
    impact TEXT, requester TEXT, status TEXT, note TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS issues (
    pk BIGSERIAL PRIMARY KEY, is_id TEXT, date TEXT, title TEXT, priority TEXT,
    owner TEXT, status TEXT, due TEXT, resolution TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS stakeholders (
    pk BIGSERIAL PRIMARY KEY, sk_id TEXT, name TEXT, role TEXT, power INTEGER,
    interest INTEGER, engage_cur TEXT, engage_target TEXT, strategy TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS decisions (
    pk BIGSERIAL PRIMARY KEY, dc_id TEXT, date TEXT, title TEXT, context TEXT,
    options TEXT, dec_text TEXT, rationale TEXT, owner TEXT, status TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS impediments (
    pk BIGSERIAL PRIMARY KEY, im_id TEXT, date TEXT, title TEXT, owner TEXT,
    severity TEXT, status TEXT, sprint INTEGER, resolved TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS lessons (
    pk BIGSERIAL PRIMARY KEY, le_id TEXT, date TEXT, sprint INTEGER, category TEXT,
    context TEXT, lesson_text TEXT, recommendation TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS raci (
    pk BIGSERIAL PRIMARY KEY, ra_id TEXT, activity TEXT, resp TEXT, acc TEXT,
    cons TEXT, inf TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS story_map (
    pk BIGSERIAL PRIMARY KEY, sm_id TEXT, activity TEXT, release_id TEXT,
    story TEXT, task TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS poker (
    pk BIGSERIAL PRIMARY KEY, pk_id TEXT, task TEXT, title TEXT, votes TEXT,
    result TEXT, status TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS portfolio (
    pk BIGSERIAL PRIMARY KEY, po_id TEXT, name TEXT, status TEXT, health DOUBLE PRECISION,
    velocity DOUBLE PRECISION, budget DOUBLE PRECISION, spent DOUBLE PRECISION,
    progress DOUBLE PRECISION, owner TEXT, note TEXT, ord INTEGER
);
