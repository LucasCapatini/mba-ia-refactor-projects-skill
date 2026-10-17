"""Controller de categorias (PB-03/PB-05): separado do módulo de relatórios, mesmos paths."""
from flask import request, jsonify

from services import category_service
from validators import category_validator


def get_categories():
    rows = category_service.list_categories_with_task_count()
    return jsonify([category.to_dict(task_count=task_count) for category, task_count in rows]), 200


def create_category():
    payload = category_validator.validate_create(request.get_json(silent=True))
    category = category_service.create_category(payload)
    return jsonify(category.to_dict()), 201


def update_category(category_id):
    category = category_service.get_category(category_id)
    payload = category_validator.validate_update(request.get_json(silent=True))
    category = category_service.update_category(category, payload)
    return jsonify(category.to_dict()), 200


def delete_category(category_id):
    category = category_service.get_category(category_id)
    category_service.delete_category(category)
    return jsonify({'message': 'Categoria deletada'}), 200
