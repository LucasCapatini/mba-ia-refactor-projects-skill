'use strict';

const sqlite3 = require('sqlite3');

/**
 * Abre UMA conexão SQLite e devolve um wrapper em Promises.
 * Para `:memory:` é obrigatório reutilizar esta única instância: cada
 * `new Database(':memory:')` seria um banco diferente.
 */
function connect(path) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(path, (err) => {
            if (err) return reject(err);
            raw.run('PRAGMA foreign_keys = ON', (pragmaErr) => {
                if (pragmaErr) return reject(pragmaErr);
                resolve(wrap(raw));
            });
        });
    });
}

function wrap(raw) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
    const exec = (sql) => new Promise((resolve, reject) => {
        raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    // Fila de transações: numa única conexão, duas transações não podem se sobrepor.
    let queue = Promise.resolve();
    const transaction = (work) => {
        const execution = queue.then(async () => {
            await exec('BEGIN');
            try {
                const result = await work();
                await exec('COMMIT');
                return result;
            } catch (err) {
                await exec('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        queue = execution.catch(() => {});
        return execution;
    };

    return { run, get, all, exec, close, transaction };
}

module.exports = { connect };
