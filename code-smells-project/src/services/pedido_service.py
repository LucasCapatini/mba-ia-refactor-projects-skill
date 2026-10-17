"""Casos de uso de pedidos: criação transacional com baixa de estoque, listagem e status."""
import logging

from src.database import transaction
from src.domain.constants import STATUS_PEDIDO_INICIAL
from src.domain.exceptions import BusinessRuleError
from src.models import pedido_model, produto_model, usuario_model
from src.services import notificacao_service

logger = logging.getLogger(__name__)


def criar_pedido(usuario_id, itens):
    """Valida estoque, calcula o total, grava pedido + itens e baixa o estoque em uma transação."""
    with transaction():
        if not usuario_model.exists(usuario_id):
            raise BusinessRuleError("Usuário " + str(usuario_id) + " não encontrado")

        produtos = produto_model.get_many_by_ids([item["produto_id"] for item in itens])
        total = 0
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise BusinessRuleError("Produto " + str(item["produto_id"]) + " não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * item["quantidade"])

        pedido_id = pedido_model.create(usuario_id, STATUS_PEDIDO_INICIAL, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.add_item(pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            if not produto_model.decrement_stock(item["produto_id"], item["quantidade"]):
                raise BusinessRuleError("Estoque insuficiente para " + produto["nome"])

    logger.info("Pedido %s criado para usuário %s", pedido_id, usuario_id)
    notificacao_service.notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos():
    return pedido_model.list_all()


def listar_por_usuario(usuario_id):
    return pedido_model.list_by_user(usuario_id)


def atualizar_status(pedido_id, novo_status):
    pedido_model.update_status(pedido_id, novo_status)
    notificacao_service.notificar_mudanca_status(pedido_id, novo_status)
    return True
