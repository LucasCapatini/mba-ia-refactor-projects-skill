// Logger mínimo com níveis. Nunca registre senha, cartão completo ou chaves.
const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[config.logLevel] ?? LEVELS.info;

const log = (level) => (...args) => {
  if (LEVELS[level] > current) return;
  const output = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
  output(`[${new Date().toISOString()}] [${level}]`, ...args);
};

module.exports = {
  error: log('error'),
  warn: log('warn'),
  info: log('info'),
  debug: log('debug'),
};
