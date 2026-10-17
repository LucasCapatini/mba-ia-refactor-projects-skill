"""Configuração da aplicação lida de variáveis de ambiente, com defaults seguros.

Nenhum segredo real deve viver aqui: use um arquivo `.env` (nunca versionado)
baseado em `.env.example`, ou exporte as variáveis no ambiente.
"""
import os


def _bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = _bool("DEBUG")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    APP_ENV = os.environ.get("APP_ENV", "development")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    # Rotas administrativas perigosas ficam desligadas por padrão (respondem 403).
    ADMIN_SQL_ENABLED = _bool("ADMIN_SQL_ENABLED")
    ADMIN_RESET_ENABLED = _bool("ADMIN_RESET_ENABLED")
