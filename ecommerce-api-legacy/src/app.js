// Composition root (createApp) e entry point (start). Importar este módulo não abre porta
// nem toca o banco: o servidor só sobe com `npm start` / `node src/app.js`.
const express = require('express');
const config = require('./config');
const { connect } = require('./database/connection');
const { createTables } = require('./database/schema');
const { seed } = require('./database/seed');
const { buildRoutes } = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const logger = require('./utils/logger');

function createApp({ db }) {
  const app = express();
  app.use(express.json());
  app.use('/api', buildRoutes({ db }));
  app.use(errorHandler);
  return app;
}

async function start() {
  const db = await connect(config.dbPath);
  await createTables(db);
  await seed(db);

  const app = createApp({ db });
  return app.listen(config.port, config.host, () => {
    logger.info(`LMS API rodando em http://${config.host}:${config.port}`);
  });
}

if (require.main === module) {
  start().catch((err) => {
    logger.error('Falha ao iniciar a aplicação:', err);
    process.exitCode = 1;
  });
}

module.exports = { createApp, start };
