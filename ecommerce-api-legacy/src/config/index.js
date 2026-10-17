'use strict';

/**
 * Configuração da aplicação lida de variáveis de ambiente.
 * Nenhum segredo real vive aqui: os defaults são seguros/vazios.
 * Em Node >= 20.6 um arquivo .env pode ser carregado com `node --env-file=.env src/app.js`.
 */

const toInt = (value, fallback) => {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : fallback;
};

module.exports = Object.freeze({
    port: toInt(process.env.PORT, 3000),
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    approvedCardPrefix: process.env.APPROVED_CARD_PREFIX || '4',
    logLevel: process.env.LOG_LEVEL || 'info',
});
