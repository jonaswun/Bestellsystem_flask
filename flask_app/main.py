"""
Main Flask application for the ordering system.
Refactored to use modular architecture with separate routes and services.
"""
import os
import logging

from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from config import Config
from routes.menu_routes import menu_bp
from routes.order_routes import order_bp
from routes.analytics_routes import analytics_bp
from services.order_service import OrderService
from utils.logging_config import setup_logging


def create_app():
    """Create and configure Flask application"""

    # Configured here too (not just in main()) so app factory works standalone
    # under WSGI servers like gunicorn that never call main().
    setup_logging(Config.LOG_LEVEL, Config.LOG_DIR)

    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    log = logging.getLogger(__name__)
    if not Config.MOCK_PRINTER and (not Config.FOOD_PRINTER_IP or not Config.DRINKS_PRINTER_IP):
        log.warning(
            "FOOD_PRINTER_IP and/or DRINKS_PRINTER_IP is not set — printing will stay "
            "unavailable until configured (see .env.example)."
        )

    # Single shared OrderService instance — one queue, one print thread
    app.order_service = OrderService()

    # Register blueprints BEFORE Swagger init so all routes are discovered
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(analytics_bp)

    # Configure Swagger UI — must come after blueprint registration
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    template = {
        "swagger": "2.0",
        "info": {
            "title": "Bestellsystem Flask REST API",
            "description": "Interactive API Documentation for the Ordering & Thermal Printing System",
            "contact": {
                "name": "Development Team"
            },
            "version": "1.0.0"
        },
        "basePath": "/"
    }

    Swagger(app, config=swagger_config, template=template)

    return app


def main():
    """Main application entry point"""

    setup_logging(Config.LOG_LEVEL, Config.LOG_DIR)
    log = logging.getLogger(__name__)
    log.info("App started")

    app = create_app()
    debug_mode = Config.DEBUG or os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    app.run(
        debug=debug_mode,
        host=Config.HOST,
        port=Config.PORT
    )


if __name__ == "__main__":
    main()
