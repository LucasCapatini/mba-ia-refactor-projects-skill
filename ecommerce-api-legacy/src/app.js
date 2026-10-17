'use strict';

const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { connect } = require('./database/connection');
const { createTables } = require('./database/schema');
const { seed } = require('./database/seed');
const buildRoutes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

/** Composition root: monta a aplicação sem efeitos colaterais (não abre porta nem toca o banco). */
function createApp({ db }) {
    const app = express();
    app.use(express.json());
    app.use('/api', buildRoutes({ db }));
    app.use(errorHandler);
    return app;
}

/** Entry point: conexão única, schema e seed aguardados antes de escutar. */
async function start() {
    const db = await connect(config.dbPath);
    await createTables(db);
    await seed(db);

    const app = createApp({ db });
    return app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        logger.error('Falha ao iniciar a aplicação', err);
        process.exit(1);
    });
}

module.exports = { createApp, start };
