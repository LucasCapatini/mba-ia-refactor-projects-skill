"""Relatório de vendas: agregação única + regra de desconto por faixa."""
from src.domain.constants import FAIXAS_DESCONTO
from src.models import relatorio_model


def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0


def relatorio_vendas():
    dados = relatorio_model.agregados_pedidos()
    faturamento = dados["faturamento"]
    total_pedidos = dados["total_pedidos"]
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": dados["pendentes"],
        "pedidos_aprovados": dados["aprovados"],
        "pedidos_cancelados": dados["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
