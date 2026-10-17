"""Validação e normalização da entrada de tasks (PB-11). Uma regra, dois usos (criar/atualizar).
Nomes de campos e mensagens são os do contrato original."""
from datetime import datetime

from domain.constants import (VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH,
                              MIN_PRIORITY, MAX_PRIORITY, DEFAULT_PRIORITY, STATUS_PENDING, DATE_FORMAT)
from domain.exceptions import ValidationError


def _validate_title(title):
    if not title:
        raise ValidationError('Título é obrigatório')
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def _validate_reference(value, field):
    """user_id/category_id: None desassocia; qualquer outro valor precisa ser inteiro."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f'{field} inválido')
    return value


def _parse_date(raw, message):
    try:
        return datetime.strptime(raw, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(message)


def _normalize_tags(tags):
    if isinstance(tags, list):
        return ','.join(str(tag) for tag in tags)
    return tags


def validate_create(data):
    if not data:
        raise ValidationError('Dados inválidos')
    payload = {
        'title': _validate_title(data.get('title')),
        'description': data.get('description', ''),
        'status': _validate_status(data.get('status', STATUS_PENDING)),
        'priority': _validate_priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _validate_reference(data.get('user_id'), 'user_id'),
        'category_id': _validate_reference(data.get('category_id'), 'category_id'),
        'due_date': None,
        'tags': None,
    }
    due_date = data.get('due_date')
    if due_date:
        payload['due_date'] = _parse_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
    tags = data.get('tags')
    if tags:
        payload['tags'] = _normalize_tags(tags)
    return payload


def validate_update(data):
    if not data:
        raise ValidationError('Dados inválidos')
    payload = {}
    if 'title' in data:
        payload['title'] = _validate_title(data['title'])
    if 'description' in data:
        payload['description'] = data['description']
    if 'status' in data:
        payload['status'] = _validate_status(data['status'])
    if 'priority' in data:
        payload['priority'] = _validate_priority(data['priority'])
    if 'user_id' in data:
        payload['user_id'] = _validate_reference(data['user_id'], 'user_id')
    if 'category_id' in data:
        payload['category_id'] = _validate_reference(data['category_id'], 'category_id')
    if 'due_date' in data:
        payload['due_date'] = _parse_date(data['due_date'], 'Formato de data inválido') if data['due_date'] else None
    if 'tags' in data:
        payload['tags'] = _normalize_tags(data['tags'])
    return payload


def _optional_int(raw, field):
    if raw in (None, ''):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f'{field} deve ser numérico')


def validate_search(args):
    """Query string de GET /tasks/search: q, status, priority, user_id (nomes do contrato)."""
    return {
        'query': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': _optional_int(args.get('priority', ''), 'priority'),
        'user_id': _optional_int(args.get('user_id', ''), 'user_id'),
    }
