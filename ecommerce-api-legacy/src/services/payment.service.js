// Gateway de pagamento simulado: aprova cartões que começam com o prefixo configurado.
const config = require('../config');
const { PAYMENT_STATUS } = require('../domain/constants');
const logger = require('../utils/logger');

function authorize(cardNumber, approvedPrefix = config.approvedCardPrefix) {
  const status = cardNumber.startsWith(approvedPrefix) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  logger.debug(`Pagamento simulado: cartão final ${cardNumber.slice(-4)} -> ${status}`);
  return status;
}

module.exports = { authorize };
