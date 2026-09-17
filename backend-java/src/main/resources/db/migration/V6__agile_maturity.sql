-- Flyway V6: Agile maturity self-assessment (Scrum / Kanban / SAFe).
-- Each row is a (framework × dimension) level 1–5. The front-end generates a default set of
-- dimensions per framework and lets levels be edited. Populated on first save from the client.

CREATE TABLE IF NOT EXISTS agile_maturity (
  pk        BIGSERIAL PRIMARY KEY,
  am_id     TEXT,
  framework TEXT,
  dimension TEXT,
  level     INTEGER,
  note      TEXT,
  ord       INTEGER
);
