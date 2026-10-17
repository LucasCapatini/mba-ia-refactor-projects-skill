"""HTTP <-> domínio para pedidos."""
from flask import jsonify, request

from src.services import pedido_service
from src.validators import pedido_validator


def criar():
    dados = pedido_validator.validate_novo_pedido(request.get_json(silent=True))
    resultado = pedido_service.criar_pedido(dados["usuario_id"], dados["itens"])
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_todos():
    return jsonify({"dados": pedido_service.listar_todos(), "sucesso": True}), 200


def listar_por_usuario(usuario_id):
    return jsonify({"dados": pedido_service.listar_por_usuario(usuario_id), "sucesso": True}), 200


def atualizar_status(pedido_id):
    novo_status = pedido_validator.validate_status(request.get_json(silent=True))
    pedido_service.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
