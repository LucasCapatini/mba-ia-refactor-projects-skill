'use strict';

const logger = require('../utils/logger');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS, DEFAULT_PASSWORD } = require('../domain/constants');
const { NotFoundError, PaymentDeniedError } = require('../domain/errors');
const userModel = require('../models/user.model');
const courseModel = require('../models/course.model');
const enrollmentModel = require('../models/enrollment.model');
const paymentModel = require('../models/payment.model');
const auditLogModel = require('../models/auditLog.model');
const paymentService = require('./payment.service');

async function findOrCreateUser(db, { name, email, password }) {
    const existing = await userModel.findByEmail(db, email);
    if (existing) return existing;

    const passwordHash = hashPassword(password || DEFAULT_PASSWORD);
    const id = await userModel.create(db, { name, email, passwordHash });
    return { id, name, email };
}

/**
 * Fluxo de checkout (mesma ordem do comportamento original):
 * curso ativo → usuário existente ou novo → autorização do cartão →
 * matrícula + pagamento + auditoria em uma única transação.
 */
async function checkout(db, { name, email, password, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(db, courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const user = await findOrCreateUser(db, { name, email, password });

    const status = paymentService.authorize(cardNumber);
    if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeniedError('Pagamento recusado');

    const enrollmentId = await db.transaction(async () => {
        const newEnrollmentId = await enrollmentModel.create(db, user.id, course.id);
        await paymentModel.create(db, newEnrollmentId, course.price, status);
        await auditLogModel.log(db, `Checkout curso ${course.id} por ${user.id}`);
        return newEnrollmentId;
    });

    logger.info('Checkout concluído', { userId: user.id, courseId: course.id, enrollmentId });
    return { enrollmentId };
}

module.exports = { checkout };
