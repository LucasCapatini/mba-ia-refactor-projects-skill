// Valida parâmetros de rota de usuário.
const { ValidationError } = require('../domain/errors');
const { toPositiveInt } = require('./common.validator');

function validateUserId(params) {
  const userId = toPositiveInt(params && params.id);
  if (userId === null) throw new ValidationError();
  return userId;
}

module.exports = { validateUserId };
