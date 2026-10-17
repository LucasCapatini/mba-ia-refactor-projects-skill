"""Fonte única de "agora" em UTC (PB-12). Substitui datetime.utcnow(), deprecated no Python 3.12+."""
from datetime import datetime, timezone


def utc_now():
    """UTC naive: compatível com as colunas DateTime existentes e com os valores já gravados."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
