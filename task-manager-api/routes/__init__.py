from routes.health_routes import health_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.auth_routes import auth_bp
from routes.category_routes import category_bp
from routes.report_routes import report_bp

ALL_BLUEPRINTS = (health_bp, task_bp, user_bp, auth_bp, category_bp, report_bp)


def register_blueprints(app):
    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)
