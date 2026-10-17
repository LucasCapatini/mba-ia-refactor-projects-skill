"""Controller de usuários (PB-05)."""
from flask import request, jsonify

from services import user_service
from validators import user_validator


def get_users():
    rows = user_service.list_users_with_task_count()
    return jsonify([user.to_dict(task_count=task_count) for user, task_count in rows]), 200


def get_user(user_id):
    user = user_service.get_user(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in user_service.list_user_tasks(user_id)]
    return jsonify(data), 200


def create_user():
    payload = user_validator.validate_create(request.get_json(silent=True))
    user = user_service.create_user(payload)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = user_service.get_user(user_id)
    payload = user_validator.validate_update(request.get_json(silent=True))
    user = user_service.update_user(user, payload)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = user_service.get_user(user_id)
    user_service.delete_user(user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user_service.get_user(user_id)
    tasks = user_service.list_user_tasks(user_id)
    return jsonify([task.to_summary_dict() for task in tasks]), 200
