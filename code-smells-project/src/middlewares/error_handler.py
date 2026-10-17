"""Error handler central: exceções de domínio viram o status correspondente;
qualquer outra vira 500 genérico com log, sem vazar `str(e)` ao cliente."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http(err):
        return jsonify({"erro": err.description, "sucesso": False}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
