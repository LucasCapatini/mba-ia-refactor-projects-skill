// Relatório financeiro: agrega as linhas da consulta única por curso.
const reportModel = require('../models/report.model');
const { PAYMENT_STATUS } = require('../domain/constants');

const toStudentEntry = (row) => ({
  student: row.student_name ?? 'Unknown',
  paid: row.payment_amount ?? 0,
});

async function financialReport(db) {
  const rows = await reportModel.findFinancialRows(db);
  const byCourse = new Map();

  for (const row of rows) {
    if (!byCourse.has(row.course_id)) {
      byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
    }
    if (row.enrollment_id === null) continue;

    const entry = byCourse.get(row.course_id);
    if (row.payment_status === PAYMENT_STATUS.PAID) entry.revenue += row.payment_amount;
    entry.students.push(toStudentEntry(row));
  }

  return [...byCourse.values()];
}

module.exports = { financialReport };
