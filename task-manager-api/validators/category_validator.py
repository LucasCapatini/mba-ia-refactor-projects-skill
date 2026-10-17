"""Validação da entrada de categorias (PB-11)."""
from domain.constants import DEFAULT_COLOR
from domain.exceptions import ValidationError
from utils.helpers import is_valid_color


def _validate_color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def validate_create(data):
    if not data:
        raise ValidationError('Dados inválidos')
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return {
        'name': name,
        'description': data.get('description', ''),
        'color': _validate_color(data.get('color', DEFAULT_COLOR)),
    }


def validate_update(data):
    if not data:
        raise ValidationError('Dados inválidos')
    payload = {}
    if 'name' in data:
        if not data['name']:
            raise ValidationError('Nome é obrigatório')
        payload['name'] = data['name']
    if 'description' in data:
        payload['description'] = data['description']
    if 'color' in data:
        payload['color'] = _validate_color(data['color'])
    return payload
