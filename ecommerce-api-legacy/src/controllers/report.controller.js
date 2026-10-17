'use strict';

const reportService = require('../services/report.service');

module.exports = ({ db }) => ({
    async financialReport(req, res) {
        const report = await reportService.financialReport(db);
        res.status(200).json(report);
    },
});
