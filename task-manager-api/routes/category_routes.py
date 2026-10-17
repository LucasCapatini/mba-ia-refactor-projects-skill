"""Rotas de categorias: antes viviam no blueprint de relatórios. Paths idênticos ao contrato."""
from flask import Blueprint

from controllers import category_controller

category_bp = Blueprint('categories', __name__)

category_bp.add_url_rule('/categories', view_func=category_controller.get_categories, methods=['GET'])
category_bp.add_url_rule('/categories', view_func=category_controller.create_category, methods=['POST'])
category_bp.add_url_rule('/categories/<int:category_id>', view_func=category_controller.update_category, methods=['PUT'])
category_bp.add_url_rule('/categories/<int:category_id>', view_func=category_controller.delete_category, methods=['DELETE'])
