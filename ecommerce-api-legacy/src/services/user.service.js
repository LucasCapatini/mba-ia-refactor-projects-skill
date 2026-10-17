'use strict';

const logger = require('../utils/logger');
const userModel = require('../models/user.model');

/**
 * Remove o usuário e, por cascata (FK ON DELETE CASCADE + PRAGMA foreign_keys),
 * suas matrículas e pagamentos. Operação idempotente: devolve quantos usuários foram removidos.
 */
async function removeUser(db, userId) {
    const removed = await userModel.remove(db, userId);
    logger.info('Usuário removido', { userId, removed });
    return removed;
}

module.exports = { removeUser };
