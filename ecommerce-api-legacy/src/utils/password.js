'use strict';

const { scryptSync, randomBytes, timingSafeEqual } = require('node:crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;

/** Gera `salt:hash` com scrypt (biblioteca padrão, sem dependência nova). */
function hashPassword(password) {
    const salt = randomBytes(SALT_BYTES).toString('hex');
    const hash = scryptSync(String(password), salt, KEY_LENGTH).toString('hex');
    return `${salt}:${hash}`;
}

/** Compara em tempo constante uma senha com o valor armazenado por `hashPassword`. */
function verifyPassword(password, stored) {
    if (typeof stored !== 'string' || !stored.includes(':')) return false;
    const [salt, hash] = stored.split(':');
    const candidate = scryptSync(String(password), salt, KEY_LENGTH);
    const expected = Buffer.from(hash, 'hex');
    return candidate.length === expected.length && timingSafeEqual(candidate, expected);
}

module.exports = { hashPassword, verifyPassword };
