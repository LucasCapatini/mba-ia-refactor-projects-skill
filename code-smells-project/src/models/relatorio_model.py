"""Consultas agregadas para relatórios: uma única passagem sobre `pedidos`."""
from src.database import get_connection


def agregados_pedidos():
    row = get_connection().execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """
    ).fetchone()
    return {
        "total_pedidos": row["total_pedidos"],
        "faturamento": row["faturamento"],
        "pendentes": row["pendentes"],
        "aprovados": row["aprovados"],
        "cancelados": row["cancelados"],
    }
