"""Mapeamento método + path -> controller. Nada de lógica aqui.

Paths, métodos e nomes de endpoint são os do contrato original. Os parâmetros de rota
foram renomeados internamente (`<int:id>` -> `<int:produto_id>`), o que não altera o path externo.
"""
from flask import Blueprint

from src.controllers import (
    admin_controller,
    pedido_controller,
    produto_controller,
    relatorio_controller,
    sistema_controller,
    usuario_controller,
)

produtos_bp = Blueprint("produtos", __name__)
produtos_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
produtos_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.pesquisar, methods=["GET"])
produtos_bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produto_controller.buscar, methods=["GET"])
produtos_bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar, methods=["POST"])
produtos_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produto_controller.atualizar, methods=["PUT"])
produtos_bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produto_controller.deletar, methods=["DELETE"])

usuarios_bp = Blueprint("usuarios", __name__)
usuarios_bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar, methods=["GET"])
usuarios_bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuario_controller.buscar, methods=["GET"])
usuarios_bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar, methods=["POST"])
usuarios_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

pedidos_bp = Blueprint("pedidos", __name__)
pedidos_bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar, methods=["POST"])
pedidos_bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos, methods=["GET"])
pedidos_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido_controller.listar_por_usuario, methods=["GET"])
pedidos_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido_controller.atualizar_status, methods=["PUT"])

relatorios_bp = Blueprint("relatorios", __name__)
relatorios_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.vendas, methods=["GET"])

sistema_bp = Blueprint("sistema", __name__)
sistema_bp.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
sistema_bp.add_url_rule("/health", "health_check", sistema_controller.health, methods=["GET"])

admin_bp = Blueprint("admin", __name__)
admin_bp.add_url_rule("/admin/reset-db", "reset_database", admin_controller.reset_database, methods=["POST"])
admin_bp.add_url_rule("/admin/query", "executar_query", admin_controller.executar_query, methods=["POST"])


def register_blueprints(app):
    for bp in (produtos_bp, usuarios_bp, pedidos_bp, relatorios_bp, sistema_bp, admin_bp):
        app.register_blueprint(bp)
