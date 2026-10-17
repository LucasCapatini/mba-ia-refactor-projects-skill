'use strict';

const logger = require('../utils/logger');
const { AppError } = require('../domain/errors');

/**
 * Error handler central. Mantém o formato original das respostas de erro
 * (texto puro via `send`) e nunca expõe detalhes internos em 500.
 */
// eslint-disable-next-line no-unused-vars
module.exports = function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
        return res.status(err.statusCode).send(err.message);
    }

    // Erros do próprio Express/body-parser (ex.: JSON malformado) já trazem o status.
    const status = err.statusCode || err.status;
    if (Number.isInteger(status) && status >= 400 && status < 500) {
        return res.status(status).send('Bad Request');
    }

    logger.error('Erro não tratado', err);
    return res.status(500).send('Erro interno');
};
