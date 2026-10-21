// Schema explícito, com integridade referencial (exige PRAGMA foreign_keys = ON na conexão).
const SCHEMA_SQL = `
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    pass TEXT
  );
  CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    title TEXT,
    price REAL,
    active INTEGER
  );
  CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE
  );
  CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    amount REAL,
    status TEXT
  );
  CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    action TEXT,
    created_at DATETIME
  );
`;

async function createTables(db) {
  await db.exec(SCHEMA_SQL);
}

module.exports = { createTables };
