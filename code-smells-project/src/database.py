"""Infraestrutura de banco: conexão por requisição, schema, seeds e transações.

Nada aqui roda no import. `init_db(app)` e `seed_db(app)` são chamados
explicitamente pelo entry point (`app.py` na raiz).
"""
import logging
import sqlite3
from contextlib import contextmanager

from flask import current_app, g
from werkzeug.security import generate_password_hash

from src.domain.constants import TIPO_USUARIO_PADRAO

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    preco REAL,
    estoque INTEGER,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT,
    tipo TEXT DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    status TEXT DEFAULT 'pendente',
    total REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    preco_unitario REAL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE SET NULL
);
"""

SEED_PRODUTOS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Credenciais de desenvolvimento (fixture). São hasheadas antes de ir ao banco.
SEED_USUARIOS = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", TIPO_USUARIO_PADRAO),
    ("Maria Santos", "maria@email.com", "senha123", TIPO_USUARIO_PADRAO),
]


def get_connection():
    """Devolve a conexão da requisição atual (uma por app context, fechada no teardown)."""
    if "db" not in g:
        # isolation_level=None: autocommit; transações multi-tabela usam `transaction()`.
        conn = sqlite3.connect(current_app.config["DB_PATH"], isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_connection(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@contextmanager
def transaction():
    """Transação explícita: COMMIT ao sair sem erro, ROLLBACK em qualquer exceção."""
    conn = get_connection()
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def init_app(app):
    app.teardown_appcontext(close_connection)


def init_db(app):
    """Cria o schema (idempotente)."""
    with app.app_context():
        get_connection().executescript(SCHEMA_SQL)
    logger.info("Schema verificado em %s", app.config["DB_PATH"])


def seed_db(app):
    """Popula produtos e usuários de exemplo apenas se a tabela de produtos estiver vazia."""
    with app.app_context():
        conn = get_connection()
        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
            return False
        with transaction():
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                SEED_PRODUTOS,
            )
            conn.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in SEED_USUARIOS],
            )
    logger.info("Seeds inseridos: %d produtos, %d usuários", len(SEED_PRODUTOS), len(SEED_USUARIOS))
    return True
