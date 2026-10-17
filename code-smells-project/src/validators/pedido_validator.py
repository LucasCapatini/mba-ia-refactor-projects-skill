"""Validação de entrada de pedidos e de mudança de status."""
from src.domain.constants import STATUS_PEDIDO_VALIDOS
from src.domain.exceptions import ValidationError


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validate_novo_pedido(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not _inteiro(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ValidationError("Itens devem ser uma lista")

    itens_validos = []
    for item in itens:
        if (
            not isinstance(item, dict)
            or not _inteiro(item.get("produto_id"))
            or not _inteiro(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Item inválido: produto_id e quantidade (inteiro positivo) são obrigatórios")
        itens_validos.append({"produto_id": item["produto_id"], "quantidade": item["quantidade"]})
    return {"usuario_id": usuario_id, "itens": itens_validos}


def validate_status(dados):
    dados = dados or {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
