'use strict';

/** Encaminha rejeições de handlers async para o error handler central (Express 4). */
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
