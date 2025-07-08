import json
import os
import csv
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from Printer import Printer
from MockPrinter import MockPrinter
from order_logger import OrderLogger
from datetime import datetime
from queue import Queue
from threading import Thread

app = Flask(__name__)
CORS(app)

printer = None

# Add a mockup switch for the printer
MOCK_PRINTER = True

if MOCK_PRINTER:
    printer_food = MockPrinter()
    printer_drinks = MockPrinter()
else:
    printer_food = Printer("192.168.0.24", logo_path='Rucksackberger_solo.png')
    printer_drinks = printer_food # Printer("192.168.0.24", logo_path='Rucksackberger_solo.png')

# Load menu from JSON file
with open("menu.json", encoding="utf-8") as f:
    menu = json.load(f)
    print(menu)

# Initialize SQLite logger
order_logger = OrderLogger()

def save_order(filename, data, user_type):
    # Use SQLite logger instead of CSV
    try:
        order_id = order_logger.save_order(data, user_type)
        print(f"Order saved to database with ID: {order_id}")
        return order_id
    except Exception as e:
        print(f"Error saving order: {e}")
        # Fallback to CSV if SQLite fails
        return save_order_csv(filename, data, user_type)

def save_order_csv(filename, data, user_type):
    """Fallback CSV logging method"""
    # Ensure CSV file exists and write header if not
    write_header = not os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        if write_header:
            headers = ['timestamp', 'table_number', 'user_agent', 'items', 'comment']
            writer.writerow(headers)

        timestamp = datetime.now().isoformat()
        writer.writerow([
            timestamp,
            data.get('tableNumber', ''),
            user_type or '',
            json.dumps(data.get('orderedItems', [])),
            data.get('comment', '')
        ])
        return None

# Create a queue for orders
order_queue = Queue()

def process_orders():
    while True:
        # Peek at the first item without removing it
        if order_queue.empty():
            continue
        order = order_queue.queue[0]  # Access the first item

    
        if not printer_food.is_available() or not printer_drinks.is_available():
            print("Printer is not available, skipping order processing.")
            continue
        else:
            # Process the order
            items_food = [item for item in order['orderedItems'] if item['type'] == 'food']
            items_drinks = [item for item in order['orderedItems'] if item['type'] == 'drink']
            printer_food.print_order(order['tableNumber'], items_food, comment=order['comment'])
            printer_drinks.print_order(order['tableNumber'], items_drinks, comment=order['comment'])

            # Remove the item from the queue after successful processing
            order_queue.get()
            order_queue.task_done()

# Start a background thread to process orders
order_thread = Thread(target=process_orders, daemon=True)
order_thread.start()

@app.route("/menu", methods=["GET"])
def get_menu():
    response = make_response(jsonify(menu))
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

@app.route("/order", methods=["POST"])
def place_order():
    data = request.json
    user_agent = request.headers.get("User-Agent")

    save_order('data.csv', data, user_agent)
    print(data)
    print(user_agent)

    # Add the order to the queue
    order_queue.put(data)

    return jsonify({"message": "Order received!", "order": data})

@app.route("/orders", methods=["GET"])
def get_orders():
    """Get recent orders with optional filtering"""
    table_number = request.args.get('table', type=int)
    limit = request.args.get('limit', default=50, type=int)
    
    try:
        if table_number:
            orders = order_logger.get_orders_by_table(table_number, limit)
        else:
            orders = order_logger.get_recent_orders(limit)
        
        return jsonify({"orders": orders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order_details(order_id):
    """Get detailed information about a specific order"""
    try:
        order = order_logger.get_order(order_id)
        if order:
            return jsonify(order)
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Update the status of an order"""
    data = request.json or {}
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "Status is required"}), 400
    
    try:
        success = order_logger.update_order_status(order_id, status)
        if success:
            return jsonify({"message": "Status updated successfully"})
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analytics/sales", methods=["GET"])
def get_sales_summary():
    """Get sales analytics"""
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    try:
        summary = order_logger.get_sales_summary(date_from, date_to)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analytics/popular-items", methods=["GET"])
def get_popular_items():
    """Get most popular menu items"""
    limit = request.args.get('limit', default=10, type=int)
    
    try:
        items = order_logger.get_popular_items(limit)
        return jsonify({"popular_items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export/orders", methods=["GET"])
def export_orders():
    """Export orders to CSV"""
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        order_logger.export_to_csv(filename, date_from, date_to)
        return jsonify({"message": f"Orders exported to {filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main():
    app.run(debug=False, host='0.0.0.0')

if __name__ == "__main__":
    main()
