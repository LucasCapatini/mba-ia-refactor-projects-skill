'use strict';

const { PAYMENT_STATUS } = require('../domain/constants');
const reportModel = require('../models/report.model');

function groupByCourse(rows) {
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
        }
        const entry = byCourse.get(row.course_id);

        if (row.enrollment_id === null) continue; // curso sem matrículas

        if (row.status === PAYMENT_STATUS.PAID) {
            entry.revenue += row.amount;
        }
        entry.students.push(reportModel.toStudentEntry(row));
    }

    return [...byCourse.values()];
}

/** Relatório financeiro: [{ course, revenue, students: [{ student, paid }] }]. */
async function financialReport(db) {
    const rows = await reportModel.fetchFinancialRows(db);
    return groupByCourse(rows);
}

module.exports = { financialReport, groupByCourse };
