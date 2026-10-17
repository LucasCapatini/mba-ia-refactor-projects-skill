"""Acesso a dados de usuários. A coluna `senha` guarda apenas o hash e nunca é serializada."""
from src.database import get_connection


def to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def to_login_dict(row):
    """Forma devolvida pelo login no contrato original (sem criado_em)."""
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def get_all():
    rows = get_connection().execute("SELECT * FROM usuarios").fetchall()
    return [to_dict(row) for row in rows]


def get_by_id(usuario_id):
    row = get_connection().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return to_dict(row) if row else None


def exists(usuario_id):
    row = get_connection().execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return row is not None


def get_row_by_email(email):
    """Linha crua (inclui o hash) para uso exclusivo do serviço de autenticação."""
    return get_connection().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def create(nome, email, senha_hash, tipo):
    cursor = get_connection().execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid
