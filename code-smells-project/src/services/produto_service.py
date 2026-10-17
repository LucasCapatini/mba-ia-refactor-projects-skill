"""Casos de uso de produtos."""
import logging

from src.domain.exceptions import NotFoundError
from src.models import produto_model

logger = logging.getLogger(__name__)


def listar():
    produtos = produto_model.get_all()
    logger.debug("Listando %d produtos", len(produtos))
    return produtos


def buscar(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def pesquisar(filtros):
    return produto_model.search(**filtros)


def criar(dados):
    produto_id = produto_model.create(**dados)
    logger.info("Produto criado com id %s", produto_id)
    return produto_id


def atualizar(produto_id, dados):
    buscar(produto_id)
    produto_model.update(produto_id, **dados)
    return True


def deletar(produto_id):
    buscar(produto_id)
    produto_model.delete(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return True
