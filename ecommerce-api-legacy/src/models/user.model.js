// Acesso a dados de usuários. `db` pode ser a conexão ou o `tx` de uma transação.
async function findByEmail(db, email) {
  return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function create(db, { name, email, passwordHash }) {
  const { lastID } = await db.run(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    [name, email, passwordHash],
  );
  return lastID;
}

// Matrículas e pagamentos do usuário são removidos por ON DELETE CASCADE.
async function remove(db, userId) {
  const { changes } = await db.run('DELETE FROM users WHERE id = ?', [userId]);
  return changes;
}

module.exports = { findByEmail, create, remove };
