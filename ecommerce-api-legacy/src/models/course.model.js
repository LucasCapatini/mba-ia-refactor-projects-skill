// Acesso a dados de cursos.
const { COURSE_ACTIVE } = require('../domain/constants');

async function findActiveById(db, courseId) {
  return db.get(
    'SELECT id, title, price, active FROM courses WHERE id = ? AND active = ?',
    [courseId, COURSE_ACTIVE],
  );
}

module.exports = { findActiveById };
