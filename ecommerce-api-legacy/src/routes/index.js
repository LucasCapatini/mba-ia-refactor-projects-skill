'use strict';

const { Router } = require('express');
const checkoutRoutes = require('./checkout.routes');
const reportRoutes = require('./report.routes');
const userRoutes = require('./user.routes');

/** Monta todas as rotas da API (o prefixo `/api` é aplicado pelo composition root). */
module.exports = function buildRoutes({ db }) {
    const router = Router();

    router.use(checkoutRoutes({ db }));
    router.use(reportRoutes({ db }));
    router.use(userRoutes({ db }));

    return router;
};
