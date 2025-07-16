"""
Order-related routes for the ordering system.
"""
from flask import Blueprint, jsonify, request
from services.order_service import OrderService

order_bp = Blueprint('order', __name__)
order_service = OrderService()

@order_bp.route("/order", methods=["POST"])
def place_order():
    """Place a new order"""
    data = request.json
    user_agent = request.headers.get("User-Agent")
    
    try:
        result = order_service.process_order(data, user_agent)
        return jsonify({"message": "Order received!", "order": data, "order_id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders", methods=["GET"])
def get_orders():
    """Get recent orders with optional filtering"""
    table_number = request.args.get('table', type=int)
    limit = request.args.get('limit', default=50, type=int)
    
    try:
        orders = order_service.get_orders(table_number, limit)
        return jsonify({"orders": orders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/<int:order_id>", methods=["GET"])
def get_order_details(order_id):
    """Get detailed information about a specific order"""
    try:
        order = order_service.get_order_details(order_id)
        if order:
            return jsonify(order)
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Update the status of an order"""
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
