"""
Main Flask application for the ordering system.
Refactored to use modular architecture with separate routes and services.
"""
from flask import Flask
from flask_cors import CORS
from config import Config
from routes.menu_routes import menu_bp
from routes.order_routes import order_bp
from routes.analytics_routes import analytics_bp


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(analytics_bp)
    
    return app


def main():
    """Main application entry point"""
    app = create_app()
    app.run(
        debug=Config.DEBUG, 
        host=Config.HOST, 
        port=Config.PORT
    )


if __name__ == "__main__":
    main()
