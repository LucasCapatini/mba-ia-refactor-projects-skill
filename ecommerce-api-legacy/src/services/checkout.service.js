// Caso de uso de checkout: valida curso, autoriza pagamento e grava usuário, matrícula,
// pagamento e auditoria numa única transação (tudo ou nada).
const courseModel = require('../models/course.model');
const userModel = require('../models/user.model');
const enrollmentModel = require('../models/enrollment.model');
const paymentModel = require('../models/payment.model');
const auditLogModel = require('../models/auditLog.model');
const paymentService = require('./payment.service');
const { PAYMENT_STATUS } = require('../domain/constants');
const { NotFoundError, PaymentDeniedError } = require('../domain/errors');
const { hashPassword, generateUnusablePassword } = require('../utils/password');

async function checkout(db, { name, email, password, courseId, cardNumber }) {
  const course = await courseModel.findActiveById(db, courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');

  const status = paymentService.authorize(cardNumber);
  if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeniedError();

  return db.transaction(async (tx) => {
    const existing = await userModel.findByEmail(tx, email);
    const userId = existing
      ? existing.id
      : await userModel.create(tx, {
        name,
        email,
        // Sem `pwd`, a conta recebe uma senha aleatória que ninguém conhece (nunca um literal).
        passwordHash: await hashPassword(password || generateUnusablePassword()),
      });

    const enrollmentId = await enrollmentModel.create(tx, userId, course.id);
    await paymentModel.create(tx, enrollmentId, course.price, status);
    await auditLogModel.log(tx, `Checkout curso ${course.id} por ${userId}`);
    return { enrollmentId };
  });
}

module.exports = { checkout };
