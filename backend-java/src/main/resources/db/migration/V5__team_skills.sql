-- Flyway V5: Star Map — team competencies by role.
-- Each row is a (member × competency) level 1–5; the front-end generates a default set from
-- each member's role and lets it be edited. Populated on first save from the client.

CREATE TABLE IF NOT EXISTS skills (
  pk     BIGSERIAL PRIMARY KEY,
  sk_id  TEXT,
  member TEXT,
  role   TEXT,
  skill  TEXT,
  level  INTEGER,
  ord    INTEGER
);
