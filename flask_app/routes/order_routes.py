"""
Order-related routes for the ordering system.
"""
import datetime
import logging
from flask import Blueprint, jsonify, request, current_app
from models import Order

order_bp = Blueprint('order', __name__)
log = logging.getLogger(__name__)


@order_bp.route("/order", methods=["POST"])
def place_order():
    """
    Place a new order
    ---
    tags:
      - Orders
    summary: Create a new order and queue for thermal printing
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - tableNumber
            - orderedItems
          properties:
            tableNumber:
              type: integer
              example: 5
            comment:
              type: string
              example: "ohne Eis"
            orderedItems:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: "Pils"
                  quantity:
                    type: integer
                    example: 2
                  price:
                    type: number
                    example: 3.50
                  type:
                    type: string
                    example: "drink"
    responses:
      200:
        description: Order successfully created and queued
      500:
        description: Error processing order
    """
    data = request.json or {}
    if 'timestamp' not in data or not data['timestamp']:
        data['timestamp'] = int(datetime.datetime.now().timestamp())
    user_agent = request.headers.get("User-Agent")

    try:
        order = Order.from_dict(data)
        order.user_agent = user_agent
        result = current_app.order_service.process_order(order, user_agent)
        log.info(f"Order placed for table {order.table_number} (order_id={result})")
        return jsonify({"message": "Order received!", "order": order.to_dict(), "order_id": result})
    except Exception as e:
        log.exception("Error placing order")
        return jsonify({"error": str(e)}), 500



@order_bp.route("/orders", methods=["GET"])
def get_orders():
    """Get recent orders with optional filtering"""
    table_number = request.args.get('table', type=int)
    limit = request.args.get('limit', default=50, type=int)

    try:
        orders = current_app.order_service.get_orders(table_number, limit)
        return jsonify({"orders": orders})
    except Exception as e:
        log.exception("Error fetching orders")
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/dashboard/food", methods=["GET"])
def get_dashboard_orders_food():
    """Get orders for the dashboard"""
    try:
        log.debug("Fetching dashboard orders")
        filter = {"key": "type", "value": "food"}
        orders = current_app.order_service.get_dashboard_orders(filter)
        return jsonify({"orders": orders})
    except Exception as e:
        log.exception("Error fetching dashboard orders")
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/dashboard/drinks", methods=["GET"])
def get_dashboard_orders_drinks():
    """Get orders for the dashboard"""
    try:
        log.debug("Fetching dashboard orders")
        # item type in order_items is recorded as 'drink' (singular)
        filter = {"key": "type", "value": "drink"}
        orders = current_app.order_service.get_dashboard_orders(filter)
        return jsonify({"orders": orders})
    except Exception as e:
        log.exception("Error fetching dashboard orders")
        return jsonify({"error": str(e)}), 500


@order_bp.route("/orders/dashboard/set_processed", methods=["PUT"])
def set_dashboard_orders_processed():
    """ Set orders as processed for the dashboard"""
    try:
        log.debug(" Setting dashboard orders as processed")
        data = request.json
        order_id = data.get("order_id")

        # item type in order_items is recorded as 'drink' (singular)
        orders = current_app.order_service.set_order_processed(order_id)
        return jsonify({"orders": orders})
    except Exception as e:
        log.exception("Error fetching dashboard orders")
        return jsonify({"error": str(e)}), 500


@order_bp.route("/orders/dashboard/complete", methods=["PUT"])
def complete_dashboard_orders():
    """
    Complete a dashboard order
    ---
    tags:
      - Orders
    summary: Mark an order as completed (persisted in the database)
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - order_id
          properties:
            order_id:
              type: integer
              example: 42
    responses:
      200:
        description: Order marked as completed
      400:
        description: Missing order_id
      404:
        description: Order not found
      500:
        description: Server error
    """
    try:
        # Validate request body exists
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        # Get and validate order_id
        data = request.json
        order_id = data.get("order_id")
        if order_id is None:
            return jsonify({"error": "order_id is required"}), 400

        log.info(f"Attempting to complete order {order_id}")

        success = current_app.order_service.complete_order(order_id)
        if not success:
            return jsonify({"success": False, "error": "Order not found"}), 404

        # Return success response
        return jsonify({
            "success": True,
            "message": f"Order {order_id} completed successfully",
            "order_id": order_id
        })

    except Exception as e:
        log.exception("Error completing order")
        return jsonify({
            "success": False,
            "error": f"Failed to complete order: {str(e)}"
        }), 500

@order_bp.route("/orders/<int:order_id>", methods=["GET"])
def get_order_details(order_id):
    """Get detailed information about a specific order"""
    try:
        order = current_app.order_service.get_order_details(order_id)
        if order:
            return jsonify(order)
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        log.exception(f"Error fetching order details for order_id={order_id}")
        return jsonify({"error": str(e)}), 500

@order_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Update the status of an order"""
    data = request.json or {}
    status = data.get('status')

    if not status:
        return jsonify({"error": "Status is required"}), 400

    try:
        success = current_app.order_service.update_order_status(order_id, status)
        if success:
            log.info(f"Order {order_id} status updated to '{status}'")
            return jsonify({"message": "Status updated successfully"})
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        log.exception(f"Error updating status for order_id={order_id}")
        return jsonify({"error": str(e)}), 500

@order_bp.route("/export/orders", methods=["GET"])
def export_orders():
    """
    Export orders to CSV
    ---
    tags:
      - Orders
    summary: Export orders (with items) to a CSV file, optionally filtered by date range
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
        description: CSV export filename
      500:
        description: Server error
    """
    date_from = request.args.get('from')
    date_to = request.args.get('to')

    try:
        filename = current_app.order_service.export_orders(date_from, date_to)
        log.info(f"Orders exported to {filename}")
        return jsonify({"message": f"Orders exported to {filename}"})
    except Exception as e:
        log.exception("Error exporting orders")
        return jsonify({"error": str(e)}), 500

@order_bp.route("/printer/status", methods=["GET"])
def get_printer_status():
    """
    Get status of printers and queue
    ---
    tags:
      - Printer
    summary: Check online availability of food and drink printers and queue size
    responses:
      200:
        description: Returns status of food_printer, drinks_printer, and pending order count
        schema:
          type: object
          properties:
            pending_orders:
              type: integer
              example: 0
            printer_status:
              type: object
              properties:
                food_printer:
                  type: object
                  properties:
                    available:
                      type: boolean
                      example: true
                    type:
                      type: string
                      example: "physical"
                drinks_printer:
                  type: object
                  properties:
                    available:
                      type: boolean
                      example: true
                    type:
                      type: string
                      example: "physical"
      500:
        description: Server error
    """
    try:
        status = current_app.order_service.get_queue_status()
        return jsonify(status)
    except Exception as e:
        log.exception("Error fetching printer status")
        return jsonify({"error": str(e)}), 500