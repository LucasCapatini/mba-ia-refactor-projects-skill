"""Rotas administrativas perigosas: continuam registradas, mas respondem 403
a menos que a flag de ambiente correspondente esteja ligada."""
from flask import current_app, jsonify, request

from src.domain.exceptions import ForbiddenError
from src.services import admin_service


def _exigir_flag(nome):
    if not current_app.config.get(nome):
        raise ForbiddenError("Endpoint desabilitado neste ambiente")


def reset_database():
    _exigir_flag("ADMIN_RESET_ENABLED")
    admin_service.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    _exigir_flag("ADMIN_SQL_ENABLED")
    dados = request.get_json(silent=True) or {}
    resultado = admin_service.executar_sql(dados.get("sql", ""))
    if resultado is not None:
        return jsonify({"dados": resultado, "sucesso": True}), 200
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
