"""Acesso a dados de produtos (SQL parametrizado). Não faz commit: a conexão está em
autocommit e operações multi-tabela são envolvidas por `database.transaction()`."""
from src.database import get_connection


def to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_all():
    rows = get_connection().execute("SELECT * FROM produtos").fetchall()
    return [to_dict(row) for row in rows]


def get_by_id(produto_id):
    row = get_connection().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return to_dict(row) if row else None


def get_many_by_ids(ids):
    """Uma única consulta para vários ids; devolve dict {id: produto}."""
    ids = list(dict.fromkeys(ids))
    if not ids:
        return {}
    placeholders = ", ".join("?" for _ in ids)
    rows = get_connection().execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids).fetchall()
    return {row["id"]: to_dict(row) for row in rows}


def create(nome, descricao, preco, estoque, categoria):
    cursor = get_connection().execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def update(produto_id, nome, descricao, preco, estoque, categoria):
    get_connection().execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    return True


def delete(produto_id):
    get_connection().execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    return True


def decrement_stock(produto_id, quantidade):
    """Baixa estoque de forma atômica; devolve False se não havia saldo suficiente."""
    cursor = get_connection().execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1


def search(termo=None, categoria=None, preco_min=None, preco_max=None):
    sql = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        sql += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        sql += " AND preco <= ?"
        params.append(preco_max)
    rows = get_connection().execute(sql, params).fetchall()
    return [to_dict(row) for row in rows]
