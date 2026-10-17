"""Casos de uso de usuários e autenticação (hash de senha com salt via Werkzeug)."""
import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.domain.constants import TIPO_USUARIO_PADRAO
from src.domain.exceptions import NotFoundError, UnauthorizedError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar():
    return usuario_model.get_all()


def buscar(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
    usuario_id = usuario_model.create(nome, email, generate_password_hash(senha), tipo)
    logger.info("Usuário criado com id %s", usuario_id)
    return usuario_id


def autenticar(email, senha):
    row = usuario_model.get_row_by_email(email)
    if row is None or not check_password_hash(row["senha"], senha):
        logger.info("Login falhou")
        raise UnauthorizedError("Email ou senha inválidos")
    logger.info("Login bem-sucedido para usuário id %s", row["id"])
    return usuario_model.to_login_dict(row)
