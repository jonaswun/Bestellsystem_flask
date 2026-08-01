"""
Main Flask application for the ordering system.
Refactored to use modular architecture with separate routes and services.
"""
import os
import logging

from flask import Flask
from flask_cors import CORS
from config import Config
from routes.menu_routes import menu_bp
from routes.order_routes import order_bp
from routes.analytics_routes import analytics_bp
from services.order_service import OrderService



def create_app():
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Single shared OrderService instance — one queue, one print thread
    app.order_service = OrderService()

    # Register blueprints
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(analytics_bp)

    return app


def main():
    """Main application entry point"""

    log = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

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
