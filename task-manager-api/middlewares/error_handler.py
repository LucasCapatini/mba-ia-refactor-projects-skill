"""Error handler central (PB-08). Mantém a chave de erro original ('error') e os status do contrato."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from domain.exceptions import DomainError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
