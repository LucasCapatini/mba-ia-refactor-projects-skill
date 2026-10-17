"""Composition root e entry point (PB-07). Importar este módulo não toca o banco nem abre porta."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Config
from database import db, init_db
from middlewares.error_handler import register_error_handlers
from routes import register_blueprints
from services.notification_service import NotificationService


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    logging.basicConfig(level=app.config['LOG_LEVEL'])

    CORS(app)
    db.init_app(app)
    app.extensions['notifications'] = NotificationService.from_config(app.config)

    register_blueprints(app)
    register_error_handlers(app)
    return app


# Instância em nível de módulo mantida por compatibilidade com scripts que fazem `from app import app, db`.
app = create_app()

if __name__ == '__main__':
    init_db(app)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
