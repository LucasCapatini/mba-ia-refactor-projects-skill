// Valida o body do checkout. Os nomes do contrato (usr, eml, pwd, c_id, card) são mapeados
// aqui para nomes internos; qualquer entrada inválida responde 400 "Bad Request", como o original.
const { ValidationError } = require('../domain/errors');
const { toPositiveInt } = require('./common.validator');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d{13,19}$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

// Cartão enviado como número JSON vira texto; acima de 2^53 o número já chegou corrompido.
function toCardNumber(card) {
  if (typeof card === 'number') return Number.isSafeInteger(card) ? String(card) : null;
  return typeof card === 'string' ? card : null;
}

function validateCheckout(body) {
  const { usr, eml, pwd, c_id: rawCourseId, card } = body || {};

  if (!usr || !eml || !rawCourseId || !card) throw new ValidationError();
  if (!isNonEmptyString(usr)) throw new ValidationError();
  if (typeof eml !== 'string' || !EMAIL_PATTERN.test(eml)) throw new ValidationError();

  const cardNumber = toCardNumber(card);
  if (cardNumber === null || !CARD_PATTERN.test(cardNumber)) throw new ValidationError();

  const courseId = toPositiveInt(rawCourseId);
  if (courseId === null) throw new ValidationError();

  const hasPassword = pwd !== undefined && pwd !== null && pwd !== '';
  if (hasPassword && typeof pwd !== 'string') throw new ValidationError();

  return {
    name: usr.trim(),
    email: eml,
    password: hasPassword ? pwd : undefined,
    courseId,
    cardNumber,
  };
}

module.exports = { validateCheckout };
