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
from routes.auth_routes import auth_bp
import secrets


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configure session management
    app.secret_key = secrets.token_hex(32)  # Generate a secure secret key
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configure CORS to allow credentials
    CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://localhost:3000'])
    
    # Register blueprints
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(auth_bp)
    
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
