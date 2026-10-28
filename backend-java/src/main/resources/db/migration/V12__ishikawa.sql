-- v1.47: editable Ishikawa (fishbone) diagram — causes of sprint schedule slippage, by category.

CREATE TABLE IF NOT EXISTS ishikawa_cats (
    pk BIGSERIAL PRIMARY KEY, name TEXT, color TEXT, side TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS ishikawa (
    pk BIGSERIAL PRIMARY KEY, ca_id TEXT, cat TEXT, cause_text TEXT,
    weight INTEGER, risk TEXT, ord INTEGER
);
