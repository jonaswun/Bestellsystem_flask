"""
Analytics-related routes for the ordering system.
"""
from flask import Blueprint, jsonify, request
from services.order_service import OrderService

analytics_bp = Blueprint('analytics', __name__)
order_service = OrderService()

@analytics_bp.route("/analytics/sales", methods=["GET"])
def get_sales_summary():
    """Get sales analytics"""
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    try:
        summary = order_service.get_sales_summary(date_from, date_to)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/analytics/popular-items", methods=["GET"])
def get_popular_items():
    """Get most popular menu items"""
    limit = request.args.get('limit', default=10, type=int)
    
    try:
        items = order_service.get_popular_items(limit)
        return jsonify({"popular_items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
