// Trilha de auditoria.
async function log(db, action) {
  await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { log };
