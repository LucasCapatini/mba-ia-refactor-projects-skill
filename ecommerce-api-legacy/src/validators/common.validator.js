// Conversões reutilizáveis pelos validators.
const POSITIVE_INT_PATTERN = /^[1-9]\d*$/;

// Aceita inteiro positivo como número ou como texto numérico; retorna null se inválido.
function toPositiveInt(value) {
  if (typeof value === 'number') return Number.isSafeInteger(value) && value > 0 ? value : null;
  if (typeof value === 'string' && POSITIVE_INT_PATTERN.test(value)) {
    const parsed = Number(value);
    return Number.isSafeInteger(parsed) ? parsed : null;
  }
  return null;
}

module.exports = { toPositiveInt };
