"""Autenticação (PB-04). Token opaco aleatório no lugar do 'fake-jwt-token-<id>' previsível."""
import logging
import secrets

from domain.exceptions import UnauthorizedError, ForbiddenError
from services.user_service import get_user_by_email

logger = logging.getLogger(__name__)


def login(email, password):
    user = get_user_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    token = secrets.token_urlsafe(32)
    logger.info('Login realizado: user_id=%s', user.id)
    return user, token
