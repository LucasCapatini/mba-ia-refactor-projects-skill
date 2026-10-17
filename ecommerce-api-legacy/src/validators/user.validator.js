'use strict';

const { ValidationError } = require('../domain/errors');

/** Parâmetro de rota `:id` deve ser um inteiro positivo. */
function validateUserId(rawId) {
    const id = Number(rawId);
    if (!Number.isInteger(id) || id <= 0) throw new ValidationError('Bad Request');
    return id;
}

module.exports = { validateUserId };
