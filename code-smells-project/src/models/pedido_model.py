"""Acesso a dados de pedidos e itens. Listagens usam um único JOIN (sem N+1)."""
from src.database import get_connection

_LISTAGEM_SQL = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    {where}
    ORDER BY p.id, i.id
"""


def _agrupar(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["pedido_id"])
        if pedido is None:
            pedido = {
                "id": row["pedido_id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["pedido_id"]] = pedido
        if row["quantidade"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_nome"] is not None else "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def list_all():
    rows = get_connection().execute(_LISTAGEM_SQL.format(where="")).fetchall()
    return _agrupar(rows)


def list_by_user(usuario_id):
    rows = get_connection().execute(_LISTAGEM_SQL.format(where="WHERE p.usuario_id = ?"), (usuario_id,)).fetchall()
    return _agrupar(rows)


def create(usuario_id, status, total):
    cursor = get_connection().execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total),
    )
    return cursor.lastrowid


def add_item(pedido_id, produto_id, quantidade, preco_unitario):
    get_connection().execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def update_status(pedido_id, novo_status):
    get_connection().execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    return True
