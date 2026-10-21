// HTTP ↔ relatório financeiro.
const reportService = require('../services/report.service');

function createReportController({ db }) {
  return {
    async financialReport(req, res) {
      res.json(await reportService.financialReport(db));
    },
  };
}

module.exports = { createReportController };
