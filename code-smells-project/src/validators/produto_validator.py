"""Validação de entrada de produtos. Uma regra, usada por criar e atualizar.

Mensagens e ordem de verificação preservam as do contrato original.
"""
from src.domain.constants import CATEGORIAS_VALIDAS, CATEGORIA_PADRAO, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.domain.exceptions import ValidationError


def _numero(valor, rotulo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(f"{rotulo} deve ser numérico")
    return valor


def _opcional_float(valor, rotulo):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"{rotulo} deve ser numérico")


def validate_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = _numero(dados["preco"], "Preço")
    estoque = _numero(dados["estoque"], "Estoque")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if descricao is None:
        descricao = ""
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validate_filtros_busca(args):
    """Query string de /produtos/busca: q, categoria, preco_min, preco_max."""
    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria") or None,
        "preco_min": _opcional_float(args.get("preco_min"), "preco_min"),
        "preco_max": _opcional_float(args.get("preco_max"), "preco_max"),
    }
