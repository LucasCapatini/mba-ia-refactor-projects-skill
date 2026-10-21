// Hash de senha com scrypt + salt aleatório (somente node:crypto).
const { scrypt, randomBytes, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');

const scryptAsync = promisify(scrypt);
const KEY_LENGTH = 64;

async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const hash = await scryptAsync(password, salt, KEY_LENGTH);
  return `${salt}:${hash.toString('hex')}`;
}

async function verifyPassword(password, stored) {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const expected = Buffer.from(hash, 'hex');
  const candidate = await scryptAsync(password, salt, expected.length);
  return timingSafeEqual(candidate, expected);
}

// Senha que ninguém conhece: a conta existe, mas não aceita login por senha.
function generateUnusablePassword() {
  return randomBytes(32).toString('base64url');
}

module.exports = { hashPassword, verifyPassword, generateUnusablePassword };
