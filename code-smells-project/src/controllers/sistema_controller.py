"""Rotas de sistema: raiz e health check (sem segredos na resposta)."""
from flask import current_app, jsonify

from src.domain.constants import APP_VERSION
from src.services import admin_service


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": admin_service.health(),
        "versao": APP_VERSION,
        "ambiente": current_app.config["APP_ENV"],
    }), 200
