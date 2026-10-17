"""HTTP <-> domínio para relatórios."""
from flask import jsonify

from src.services import relatorio_service


def vendas():
    return jsonify({"dados": relatorio_service.relatorio_vendas(), "sucesso": True}), 200
