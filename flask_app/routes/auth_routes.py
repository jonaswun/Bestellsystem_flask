"""
Authentication routes for user login/logout functionality.
"""
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'customer')  # Default role
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    try:
        user_id = auth_service.create_user(username, password, email, role)
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Login user"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    try:
        user = auth_service.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route("/auth/logout", methods=["POST"])
@login_required
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logout successful'})

@auth_bp.route("/auth/profile", methods=["GET"])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        user = auth_service.get_user_by_id(session['user_id'])
        if user:
            return jsonify({
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'created_at': user['created_at']
                }
            })
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_bp.route("/auth/check", methods=["GET"])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        try:
            user = auth_service.get_user_by_id(session['user_id'])
            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'role': user['role']
                    }
                })
        except Exception:
            session.clear()
    
    return jsonify({'authenticated': False})

@auth_bp.route("/auth/users", methods=["GET"])
@login_required
def get_users():
    """Get all users (admin only)"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        users = auth_service.get_all_users()
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': 'Failed to get users'}), 500
