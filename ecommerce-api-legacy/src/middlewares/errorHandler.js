// Error handler central. Mantém o formato original das respostas de erro (texto puro).
const { AppError } = require('../domain/errors');
const logger = require('../utils/logger');

// eslint-disable-next-line no-unused-vars
module.exports = function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);

  // JSON malformado no body (express.json)
  if (err && err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');

  logger.error(`${req.method} ${req.originalUrl} falhou:`, err);
  return res.status(500).send('Erro interno');
};
