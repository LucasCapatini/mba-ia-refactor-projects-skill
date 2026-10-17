'use strict';

const { UNKNOWN_STUDENT } = require('../domain/constants');

/**
 * Uma única consulta substitui o N+1 (cursos → matrículas → usuário + pagamento).
 * Cursos sem matrícula aparecem com `enrollment_id` nulo.
 */
async function fetchFinancialRows(db) {
    return db.all(`
        SELECT c.id      AS course_id,
               c.title   AS title,
               e.id      AS enrollment_id,
               u.name    AS student,
               p.amount  AS amount,
               p.status  AS status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u       ON u.id = e.user_id
        LEFT JOIN payments p    ON p.enrollment_id = e.id
        ORDER BY c.id, e.id
    `);
}

/** Serialização única de um aluno dentro do relatório (chaves do contrato: student, paid). */
function toStudentEntry(row) {
    return {
        student: row.student ?? UNKNOWN_STUDENT,
        paid: row.amount ?? 0,
    };
}

module.exports = { fetchFinancialRows, toStudentEntry };
