// Monta todas as rotas sob o prefixo /api.
const express = require('express');
const { buildCheckoutRoutes } = require('./checkout.routes');
const { buildReportRoutes } = require('./report.routes');
const { buildUserRoutes } = require('./user.routes');

function buildRoutes({ db }) {
  const router = express.Router();
  router.use(buildCheckoutRoutes({ db }));
  router.use(buildReportRoutes({ db }));
  router.use(buildUserRoutes({ db }));
  return router;
}

module.exports = { buildRoutes };
