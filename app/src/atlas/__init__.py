"""
Application Factory for Project Atlas.
"""

from flask import Flask

from atlas.api import (
    health_bp,
    home_bp,
    info_bp,
    version_bp,
)
from atlas.config import Config
from atlas.logging_config import configure_logging, init_request_logging
from atlas.metrics import init_metrics


def create_app():
    """
    Create and configure the Flask application.
    """

    configure_logging()
    app = Flask(__name__)

    app.config.from_object(Config)

    app.register_blueprint(home_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(info_bp)
    app.register_blueprint(version_bp)
    init_request_logging(app)
    init_metrics(app)

    return app
