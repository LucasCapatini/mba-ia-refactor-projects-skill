// Configuração lida do ambiente, com defaults seguros para desenvolvimento local.
const toInt = (value, fallback) => {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
};

module.exports = Object.freeze({
  port: toInt(process.env.PORT, 3000),
  host: process.env.HOST || '127.0.0.1',
  dbPath: process.env.DB_PATH || ':memory:',
  // Gateway simulado: cartões que começam com este prefixo são aprovados.
  approvedCardPrefix: process.env.APPROVED_CARD_PREFIX || '4',
  logLevel: process.env.LOG_LEVEL || 'info',
});
