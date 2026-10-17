"""Entry point. Uso: `python app.py` (variáveis de ambiente em .env.example)."""
import logging

from src.app import create_app
from src.config.settings import Config
from src.database import init_db, seed_db

app = create_app()

if __name__ == "__main__":
    init_db(app)
    seed_db(app)
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", Config.HOST, Config.PORT)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
