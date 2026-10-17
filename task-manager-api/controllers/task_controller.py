"""Controller de tasks (PB-05): lê request, chama validator + service, monta a resposta."""
from flask import request, jsonify

from services import task_service
from validators import task_validator


def get_tasks():
    tasks = task_service.list_tasks()
    return jsonify([task.to_dict(with_overdue=True, with_relations=True) for task in tasks]), 200


def get_task(task_id):
    task = task_service.get_task(task_id)
    return jsonify(task.to_dict(with_overdue=True)), 200


def create_task():
    payload = task_validator.validate_create(request.get_json(silent=True))
    task = task_service.create_task(payload)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = task_service.get_task(task_id)
    payload = task_validator.validate_update(request.get_json(silent=True))
    task = task_service.update_task(task, payload)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = task_service.get_task(task_id)
    task_service.delete_task(task)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    filters = task_validator.validate_search(request.args)
    tasks = task_service.search_tasks(filters)
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(task_service.task_stats()), 200
