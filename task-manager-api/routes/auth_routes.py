from flask import Blueprint

from controllers import auth_controller

auth_bp = Blueprint('auth', __name__)

auth_bp.add_url_rule('/login', view_func=auth_controller.login, methods=['POST'])
