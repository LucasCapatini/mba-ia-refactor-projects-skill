// Erros de domínio: o error handler central converte statusCode + message em resposta.
class AppError extends Error {
  constructor(message, statusCode = 400) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
  }
}

class ValidationError extends AppError {
  constructor(message = 'Bad Request') { super(message, 400); }
}

class NotFoundError extends AppError {
  constructor(message) { super(message, 404); }
}

// O contrato original responde 400 para pagamento recusado.
class PaymentDeniedError extends AppError {
  constructor(message = 'Pagamento recusado') { super(message, 400); }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeniedError };
