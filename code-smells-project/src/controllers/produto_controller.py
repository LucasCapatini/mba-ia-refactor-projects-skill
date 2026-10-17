"""HTTP <-> domínio para produtos. Sem SQL, sem regra de negócio, sem try/except."""
from flask import jsonify, request

from src.services import produto_service
from src.validators import produto_validator


def listar():
    return jsonify({"dados": produto_service.listar(), "sucesso": True}), 200


def buscar(produto_id):
    return jsonify({"dados": produto_service.buscar(produto_id), "sucesso": True}), 200


def pesquisar():
    filtros = produto_validator.validate_filtros_busca(request.args)
    resultados = produto_service.pesquisar(filtros)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar():
    dados = produto_validator.validate_produto(request.get_json(silent=True))
    produto_id = produto_service.criar(dados)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(produto_id):
    produto_service.buscar(produto_id)  # 404 antes da validação, como no contrato original
    dados = produto_validator.validate_produto(request.get_json(silent=True))
    produto_service.atualizar(produto_id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id):
    produto_service.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
