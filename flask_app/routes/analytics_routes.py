"""
Analytics-related routes for the ordering system.
"""
from flask import Blueprint, jsonify, request, session
from services.order_service import OrderService
from functools import wraps

analytics_bp = Blueprint('analytics', __name__)
order_service = OrderService()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Decorator to require staff-level access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        if session.get('role', 'customer') not in ['staff', 'manager', 'admin']:
            return jsonify({'error': 'Staff access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route("/analytics/sales", methods=["GET"])
@staff_required
def get_sales_summary():
    """Get sales analytics (staff only)"""
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    try:
        summary = order_service.get_sales_summary(date_from, date_to)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/analytics/popular-items", methods=["GET"])
@staff_required
def get_popular_items():
    """Get most popular menu items (staff only)"""
    limit = request.args.get('limit', default=10, type=int)
    
    try:
        items = order_service.get_popular_items(limit)
        return jsonify({"popular_items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/analytics/user-activity", methods=["GET"])
@staff_required
def get_user_activity():
    """Get user activity analytics (staff only)"""
    try:
        activity = order_service.get_user_activity_stats()
        return jsonify({"user_activity": activity})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/analytics/my-orders", methods=["GET"])
@login_required
def get_my_order_stats():
    """Get current user's order statistics"""
    user_id = session['user_id']
    
    try:
        stats = order_service.get_user_order_stats(user_id)
        return jsonify({"order_stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
