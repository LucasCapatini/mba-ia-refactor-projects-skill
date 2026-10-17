'use strict';

/** Projeção pública: nunca inclui a coluna `pass`. */
const PUBLIC_COLUMNS = 'id, name, email';

async function findByEmail(db, email) {
    return db.get(`SELECT ${PUBLIC_COLUMNS} FROM users WHERE email = ?`, [email]);
}

async function create(db, { name, email, passwordHash }) {
    const { lastID } = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passwordHash],
    );
    return lastID;
}

/** Remove o usuário; matrículas e pagamentos caem em cascata (FK ON DELETE CASCADE). */
async function remove(db, id) {
    const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
    return changes;
}

module.exports = { findByEmail, create, remove };
