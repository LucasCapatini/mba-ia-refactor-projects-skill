"""Validação da entrada de usuários e login (PB-11)."""
from domain.constants import VALID_ROLES, DEFAULT_ROLE, MIN_PASSWORD_LENGTH
from domain.exceptions import ValidationError
from utils.helpers import validate_email


def _validate_email(email):
    if not validate_email(email):
        raise ValidationError('Email inválido')
    return email


def _validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_create(data):
    if not data:
        raise ValidationError('Dados inválidos')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    _validate_email(email)
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    _validate_role(role)
    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_update(data):
    if not data:
        raise ValidationError('Dados inválidos')
    payload = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise ValidationError('Nome é obrigatório')
        payload['name'] = data['name']
    if 'email' in data:
        payload['email'] = _validate_email(data['email'])
    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        payload['password'] = data['password']
    if 'role' in data:
        payload['role'] = _validate_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('active deve ser booleano')
        payload['active'] = data['active']
    return payload


def validate_login(data):
    if not data:
        raise ValidationError('Dados inválidos')
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return {'email': email, 'password': password}
