"""
Order-related routes for the ordering system.
"""
from flask import Blueprint, jsonify, request, session
from services.order_service import OrderService
from functools import wraps

order_bp = Blueprint('order', __name__)
order_service = OrderService()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@order_bp.route("/order", methods=["POST"])
@login_required
def place_order():
    """Place a new order"""
    data = request.json
    user_agent = request.headers.get("User-Agent")
    
    # Add user information to the order
    user_info = {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    }
    
    try:
        result = order_service.process_order(data, user_agent, user_info)
        return jsonify({"message": "Order received!", "order": data, "order_id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders", methods=["GET"])
@login_required
def get_orders():
    """Get recent orders with optional filtering"""
    table_number = request.args.get('table', type=int)
    limit = request.args.get('limit', default=50, type=int)
    user_role = session.get('role', 'customer')
    user_id = session.get('user_id')
    
    try:
        # Customers can only see their own orders, staff and above can see all
        if user_role == 'customer':
            orders = order_service.get_orders_by_user(user_id, limit)
        else:
            orders = order_service.get_orders(table_number, limit)
        return jsonify({"orders": orders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order_details(order_id):
    """Get detailed information about a specific order"""
    user_role = session.get('role', 'customer')
    user_id = session.get('user_id')
    
    try:
        order = order_service.get_order_details(order_id)
        if order:
            # Check if user has permission to view this order
            if user_role == 'customer' and order.get('user_id') != user_id:
                return jsonify({"error": "Access denied"}), 403
            return jsonify(order)
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def update_order_status(order_id):
    """Update the status of an order (staff only)"""
    user_role = session.get('role', 'customer')
    
    # Only staff, managers, and admins can update order status
    if user_role not in ['staff', 'manager', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.json or {}
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "Status is required"}), 400
    
    try:
        success = order_service.update_order_status(order_id, status)
        if success:
            return jsonify({"message": "Status updated successfully"})
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/export/orders", methods=["GET"])
def export_orders():
    """Export orders to CSV"""
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    try:
        filename = order_service.export_orders(date_from, date_to)
        return jsonify({"message": f"Orders exported to {filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
