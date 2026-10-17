'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { PAYMENT_STATUS } = require('../domain/constants');

/**
 * Gateway simulado: aprova cartões cujo número começa com o prefixo configurado.
 * Nunca registra o número do cartão nem a chave do gateway.
 */
function authorize(cardNumber) {
    logger.debug('Autorizando pagamento', { gatewayConfigured: Boolean(config.paymentGatewayKey) });
    return String(cardNumber).startsWith(config.approvedCardPrefix)
        ? PAYMENT_STATUS.PAID
        : PAYMENT_STATUS.DENIED;
}

module.exports = { authorize };
