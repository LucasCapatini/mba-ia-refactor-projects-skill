// Uma única conexão sqlite3 (obrigatório com ':memory:': cada nova conexão seria outro banco),
// exposta em Promises. Todas as operações passam por uma fila, para que uma transação em
// andamento não seja intercalada com comandos de outra requisição na mesma conexão.
const sqlite3 = require('sqlite3');

function wrap(raw) {
  return {
    run: (sql, params = []) => new Promise((resolve, reject) => {
      raw.run(sql, params, function onRun(err) {
        if (err) return reject(err);
        return resolve({ lastID: this.lastID, changes: this.changes });
      });
    }),
    get: (sql, params = []) => new Promise((resolve, reject) => {
      raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    }),
    all: (sql, params = []) => new Promise((resolve, reject) => {
      raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    }),
    exec: (sql) => new Promise((resolve, reject) => {
      raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    }),
  };
}

function createQueue() {
  let tail = Promise.resolve();
  return (task) => {
    const result = tail.then(task);
    tail = result.catch(() => {});
    return result;
  };
}

function connect(path) {
  return new Promise((resolve, reject) => {
    const raw = new sqlite3.Database(path, (openErr) => {
      if (openErr) return reject(openErr);

      const direct = wrap(raw);
      const exclusive = createQueue();

      const db = {
        run: (sql, params) => exclusive(() => direct.run(sql, params)),
        get: (sql, params) => exclusive(() => direct.get(sql, params)),
        all: (sql, params) => exclusive(() => direct.all(sql, params)),
        exec: (sql) => exclusive(() => direct.exec(sql)),
        // fn recebe `tx` com a mesma interface (run/get/all) executando dentro da transação.
        transaction: (fn) => exclusive(async () => {
          await direct.exec('BEGIN IMMEDIATE');
          try {
            const result = await fn(direct);
            await direct.exec('COMMIT');
            return result;
          } catch (err) {
            await direct.exec('ROLLBACK');
            throw err;
          }
        }),
        close: () => exclusive(() => new Promise((res, rej) => raw.close((err) => (err ? rej(err) : res())))),
      };

      return db.exec('PRAGMA foreign_keys = ON').then(() => resolve(db), reject);
    });
  });
}

module.exports = { connect };
