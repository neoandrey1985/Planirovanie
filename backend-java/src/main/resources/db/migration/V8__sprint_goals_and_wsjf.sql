CREATE TABLE IF NOT EXISTS sprint_goals (
    pk BIGSERIAL PRIMARY KEY,
    sg_id TEXT,
    sprint INTEGER,
    goal TEXT,
    status TEXT,
    ord INTEGER
);

CREATE TABLE IF NOT EXISTS wsjf (
    pk BIGSERIAL PRIMARY KEY,
    w_id TEXT,
    task TEXT,
    name TEXT,
    bv INTEGER,
    tc INTEGER,
    rr INTEGER,
    job_size DOUBLE PRECISION,
    ord INTEGER
);
