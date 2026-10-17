'use strict';

async function findActiveById(db, id) {
    return db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
}

async function create(db, { title, price, active = 1 }) {
    const { lastID } = await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
        [title, price, active],
    );
    return lastID;
}

module.exports = { findActiveById, create };
