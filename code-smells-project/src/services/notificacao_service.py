"""Notificações de pedido. Hoje apenas registra em log (sem integração real e sem PII)."""
import logging

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("EMAIL: pedido %s criado para usuário %s", pedido_id, usuario_id)
    logger.info("SMS: pedido %s recebido", pedido_id)
    logger.info("PUSH: novo pedido %s recebido pelo sistema", pedido_id)


def notificar_mudanca_status(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("NOTIFICAÇÃO: pedido %s aprovado, preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("NOTIFICAÇÃO: pedido %s cancelado, devolver estoque", pedido_id)
