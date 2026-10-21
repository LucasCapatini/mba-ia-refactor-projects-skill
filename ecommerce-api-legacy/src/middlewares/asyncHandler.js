// Express 4 não captura rejeições de handlers async: encaminha para o error handler.
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
