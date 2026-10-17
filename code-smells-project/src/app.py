"""Composition root: monta a aplicação sem efeitos colaterais (não sobe servidor,
não cria tabelas). Schema e seeds são responsabilidade do entry point."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Config
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import register_blueprints


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    CORS(app)
    database.init_app(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app
