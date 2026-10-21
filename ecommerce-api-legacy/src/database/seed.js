// Dados iniciais de desenvolvimento. O usuário semente recebe uma senha aleatória inutilizável:
// não existe senha conhecida (nem em texto puro) gravada no banco.
const { PAYMENT_STATUS, COURSE_ACTIVE } = require('../domain/constants');
const { hashPassword, generateUnusablePassword } = require('../utils/password');

async function seed(db) {
  const { count } = await db.get('SELECT COUNT(*) AS count FROM users');
  if (count > 0) return;

  await db.transaction(async (tx) => {
    const passwordHash = await hashPassword(generateUnusablePassword());
    const { lastID: userId } = await tx.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      ['Leonan', 'leonan@fullcycle.com.br', passwordHash],
    );
    const { lastID: courseId } = await tx.run(
      'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
      ['Clean Architecture', 997.0, COURSE_ACTIVE],
    );
    await tx.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', ['Docker', 497.0, COURSE_ACTIVE]);
    const { lastID: enrollmentId } = await tx.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseId],
    );
    await tx.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, 997.0, PAYMENT_STATUS.PAID],
    );
  });
}

module.exports = { seed };
