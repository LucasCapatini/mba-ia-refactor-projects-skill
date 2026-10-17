"""Consultas de infraestrutura usadas por health check e rotas administrativas."""
from src.database import get_connection


def contagens():
    row = get_connection().execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos)  AS pedidos
        """
    ).fetchone()
    return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}


def limpar_tabelas():
    """Apaga todos os registros, filhos antes dos pais. Deve rodar dentro de `transaction()`."""
    conn = get_connection()
    for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
        conn.execute(f"DELETE FROM {tabela}")


def executar_sql(sql):
    """Executa SQL arbitrário (recurso administrativo, protegido por flag no controller).
    Devolve a lista de linhas para SELECT ou None para os demais comandos."""
    cursor = get_connection().execute(sql)
    if sql.strip().upper().startswith("SELECT"):
        return [dict(row) for row in cursor.fetchall()]
    return None
