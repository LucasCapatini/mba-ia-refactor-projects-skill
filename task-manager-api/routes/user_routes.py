"""Rotas de usuários: só mapeiam método + path para o controller (PB-05). /login foi para auth_routes."""
from flask import Blueprint

from controllers import user_controller

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/users', view_func=user_controller.get_users, methods=['GET'])
user_bp.add_url_rule('/users', view_func=user_controller.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=user_controller.get_user, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=user_controller.update_user, methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=user_controller.delete_user, methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=user_controller.get_user_tasks, methods=['GET'])
