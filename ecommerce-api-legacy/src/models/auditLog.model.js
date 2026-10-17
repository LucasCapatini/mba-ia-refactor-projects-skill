'use strict';

async function log(db, action) {
    const { lastID } = await db.run(
        "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
        [action],
    );
    return lastID;
}

module.exports = { log };
