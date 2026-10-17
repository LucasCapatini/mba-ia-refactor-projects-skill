"""Operações administrativas e de diagnóstico. A liberação por flag fica no controller."""
import logging
import sqlite3

from src.database import transaction
from src.domain.exceptions import BusinessRuleError, ValidationError
from src.models import sistema_model

logger = logging.getLogger(__name__)


def health():
    return sistema_model.contagens()


def resetar_banco():
    with transaction():
        sistema_model.limpar_tabelas()
    logger.warning("Banco de dados resetado via rota administrativa")
    return True


def executar_sql(sql):
    if not sql:
        raise ValidationError("Query não informada")
    try:
        return sistema_model.executar_sql(sql)
    except sqlite3.Error as exc:
        # A mensagem descreve o SQL enviado pelo próprio administrador, não internals da aplicação.
        raise BusinessRuleError("Erro ao executar a query: " + str(exc))
