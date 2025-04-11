from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Initialize database before registering routes
    initialize_database()

    # Register Blueprints
    from .routes import main
    app.register_blueprint(main)

    return app