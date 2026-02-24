"""Application factory module."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()


def create_app(config_name: str = 'default') -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: The configuration environment name.

    Returns:
        The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
<<<<<<< HEAD
=======

    # Initialize default modules (skip during testing)
    if config_name != 'testing':
        with app.app_context():
            try:
                from app.utils.init_modules import init_default_modules
                init_default_modules()
            except Exception as e:
                app.logger.warning(f"Could not initialize default modules: {str(e)}")
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.tasks import tasks_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
<<<<<<< HEAD
=======
    from app.routes.admin_permissions import admin_permissions_bp
    from app.routes.scope import scope_bp
    from app.routes.schedule import schedule_bp
    from app.routes.cost import cost_bp
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp)
<<<<<<< HEAD
=======
    app.register_blueprint(admin_permissions_bp)
    app.register_blueprint(scope_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(cost_bp)
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1

    return app