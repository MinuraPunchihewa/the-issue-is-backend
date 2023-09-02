from flask import Flask
from config import DevelopmentConfig


def create_app(config=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config)

    # register main blueprint
    from app.blueprints import main as main_bp
    app.register_blueprint(main_bp)

    return app