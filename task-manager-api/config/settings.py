"""Configuração por ambiente (PB-01). Única camada que lê os.environ."""
import os

try:  # python-dotenv já está no manifesto; carrega .env se existir, sem tornar-se obrigatório
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _bool(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return int(default)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
    DEBUG = _bool('DEBUG')
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = _int('PORT', 5000)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
    SMTP_PORT = _int('SMTP_PORT', 587)
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
