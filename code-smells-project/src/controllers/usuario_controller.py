"""HTTP <-> domínio para usuários e login."""
from flask import jsonify, request

from src.services import usuario_service
from src.validators import usuario_validator


def listar():
    return jsonify({"dados": usuario_service.listar(), "sucesso": True}), 200


def buscar(usuario_id):
    return jsonify({"dados": usuario_service.buscar(usuario_id), "sucesso": True}), 200


def criar():
    dados = usuario_validator.validate_novo_usuario(request.get_json(silent=True))
    usuario_id = usuario_service.criar(dados["nome"], dados["email"], dados["senha"])
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    credenciais = usuario_validator.validate_login(request.get_json(silent=True))
    usuario = usuario_service.autenticar(credenciais["email"], credenciais["senha"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
