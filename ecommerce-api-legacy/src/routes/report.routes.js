const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { createReportController } = require('../controllers/report.controller');

function buildReportRoutes({ db }) {
  const router = express.Router();
  const controller = createReportController({ db });

  router.get('/admin/financial-report', asyncHandler(controller.financialReport));
  return router;
}

module.exports = { buildReportRoutes };
