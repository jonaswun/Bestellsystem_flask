import json
import os
import csv
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from Printer import Printer
from MockPrinter import MockPrinter
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

def save_order(filename, data, user_type):
    # Ensure CSV file exists and write header if not
    write_header = not os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        if write_header:
            headers = ['timestamp']
            for element in data['orderedItems']:
                headers.append(element)
            writer.writerow(headers)

        timestamp = datetime.now().isoformat()

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

def main():
    app.run(debug=False, host='0.0.0.0')

if __name__ == "__main__":
    main()
