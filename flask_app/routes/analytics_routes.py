"""
Analytics-related routes for the ordering system.
"""
import logging
from flask import Blueprint, jsonify, request, current_app

analytics_bp = Blueprint('analytics', __name__)
log = logging.getLogger(__name__)


@analytics_bp.route("/analytics/sales", methods=["GET"])
def get_sales_summary():
    """
    Get sales analytics summary
    ---
    tags:
      - Analytics
    summary: Get total sales per item, grouped by date range
    parameters:
      - in: query
        name: from
        type: string
        description: "Start date filter (ISO format: YYYY-MM-DD)"
        required: false
      - in: query
        name: to
        type: string
        description: "End date filter (ISO format: YYYY-MM-DD)"
        required: false
    responses:
      200:
        description: Sales summary with totals and revenue
      500:
        description: Server error
    """
    date_from = request.args.get('from')
    date_to = request.args.get('to')

    try:
        summary = current_app.order_service.get_sales_summary(date_from, date_to)
        return jsonify(summary)
    except Exception as e:
        log.exception("Error fetching sales summary")
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/analytics/popular-items", methods=["GET"])
def get_popular_items():
    """
    Get most popular menu items
    ---
    tags:
      - Analytics
    summary: Returns the top N most ordered menu items
    parameters:
      - in: query
        name: limit
        type: integer
        default: 10
        description: Maximum number of items to return
        required: false
    responses:
      200:
        description: List of popular items with order counts
        schema:
          type: object
          properties:
            popular_items:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  count:
                    type: integer
      500:
        description: Server error
    """
    limit = request.args.get('limit', default=10, type=int)

    try:
        items = current_app.order_service.get_popular_items(limit)
        return jsonify({"popular_items": items})
    except Exception as e:
        log.exception("Error fetching popular items")
        return jsonify({"error": str(e)}), 500
