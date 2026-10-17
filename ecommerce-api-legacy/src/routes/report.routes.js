'use strict';

const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const createReportController = require('../controllers/report.controller');

module.exports = ({ db }) => {
    const router = Router();
    const controller = createReportController({ db });

    router.get('/admin/financial-report', asyncHandler(controller.financialReport));

    return router;
};
