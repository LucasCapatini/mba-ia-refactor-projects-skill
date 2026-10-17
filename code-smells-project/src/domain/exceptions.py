"""Exceções de domínio. O error handler central traduz cada uma em status HTTP."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    status_code = 400


class BusinessRuleError(DomainError):
    # O contrato original respondia 400 para regras de negócio (estoque, produto inexistente).
    status_code = 400


class NotFoundError(DomainError):
    status_code = 404


class UnauthorizedError(DomainError):
    status_code = 401


class ForbiddenError(DomainError):
    status_code = 403
