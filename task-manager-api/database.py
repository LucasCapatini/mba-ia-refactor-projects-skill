"""Infraestrutura de banco: instância do ORM e inicialização explícita do schema (PB-06/PB-07)."""
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, 'connect')
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite não aplica FOREIGN KEY por padrão; liga por conexão (PB-15)."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


def init_db(app, reset=False):
    """Cria as tabelas. Chamada explicitamente pelo entry point e pelo seed, nunca no import."""
    with app.app_context():
        if reset:
            db.drop_all()
        db.create_all()


def commit():
    """Commit único por operação de negócio; em falha desfaz e propaga para o error handler (PB-08)."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
