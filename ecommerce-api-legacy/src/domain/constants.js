'use strict';

module.exports = Object.freeze({
    PAYMENT_STATUS: Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' }),
    /**
     * Senha atribuída quando o checkout não envia `pwd`.
     * Mantida por compatibilidade com o comportamento original (campo opcional no contrato);
     * agora é armazenada apenas como hash com salt.
     */
    DEFAULT_PASSWORD: '123456',
    UNKNOWN_STUDENT: 'Unknown',
});
