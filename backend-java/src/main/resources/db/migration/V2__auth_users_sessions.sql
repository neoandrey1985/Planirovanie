-- Flyway V2: server-side authentication — users, roles and sessions (PostgreSQL).
-- Roles: VIEWER (read-only), EDITOR (edit data), ADMIN (full access + user management).
-- Passwords are stored as PBKDF2WithHmacSHA256 hashes (pbkdf2$iterations$saltB64$hashB64).
-- Default users are seeded by the Java AuthService on first startup (so hashes match the
-- verifier exactly); this migration only creates the tables.

CREATE TABLE IF NOT EXISTS app_users (
  pk           BIGSERIAL PRIMARY KEY,
  username     TEXT NOT NULL UNIQUE,
  pass_hash    TEXT NOT NULL,
  role         TEXT NOT NULL,
  display_name TEXT,
  active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_sessions (
  token      TEXT PRIMARY KEY,
  username   TEXT NOT NULL,
  role       TEXT NOT NULL,
  created_at TIMESTAMP,
  expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_sessions_expires ON app_sessions (expires_at);
