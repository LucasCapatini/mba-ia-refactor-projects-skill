"""Controller de autenticação (PB-04/PB-05)."""
from flask import request, jsonify

from services import auth_service
from validators import user_validator


def login():
    credentials = user_validator.validate_login(request.get_json(silent=True))
    user, token = auth_service.login(credentials['email'], credentials['password'])
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200
