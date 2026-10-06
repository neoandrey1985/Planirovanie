-- v1.43: team health & performance — Team Health Check, deployments and incidents (DORA).

CREATE TABLE IF NOT EXISTS team_health (
    pk BIGSERIAL PRIMARY KEY, hc_id TEXT, date TEXT, sprint INTEGER,
    dimension TEXT, rating TEXT, trend TEXT, note TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS deployments (
    pk BIGSERIAL PRIMARY KEY, dp_id TEXT, date TEXT, release_id TEXT, env TEXT,
    status TEXT, lead_days DOUBLE PRECISION, note TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS incidents (
    pk BIGSERIAL PRIMARY KEY, in_id TEXT, date TEXT, title TEXT, severity TEXT,
    down_hours DOUBLE PRECISION, cause TEXT, status TEXT, postmortem TEXT, ord INTEGER
);
