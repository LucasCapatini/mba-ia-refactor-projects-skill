'use strict';

const { ValidationError } = require('../domain/errors');

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;
const CARD_PATTERN = /^\d{13,19}$/;

/**
 * Valida o body do checkout. Os nomes dos campos (`usr`, `eml`, `pwd`, `c_id`, `card`)
 * fazem parte do contrato e são mapeados para nomes internos apenas aqui.
 */
function validateCheckout(body) {
    const data = body && typeof body === 'object' ? body : {};
    const { usr, eml, pwd, c_id: rawCourseId, card } = data;

    if (!usr || !eml || !rawCourseId || !card) throw new ValidationError('Bad Request');
    if (typeof usr !== 'string' || usr.trim() === '') throw new ValidationError('Bad Request');
    if (typeof eml !== 'string' || !EMAIL_PATTERN.test(eml)) throw new ValidationError('Bad Request');

    const courseId = Number(rawCourseId);
    if (!Number.isInteger(courseId) || courseId <= 0) throw new ValidationError('Bad Request');

    const cardNumber = String(card);
    if (!CARD_PATTERN.test(cardNumber)) throw new ValidationError('Bad Request');

    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') throw new ValidationError('Bad Request');

    return {
        name: usr,
        email: eml,
        password: pwd || null,
        courseId,
        cardNumber,
    };
}

module.exports = { validateCheckout };
