import json
import os
import csv
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from Printer import Printer
from datetime import datetime

app = Flask(__name__)
CORS(app)

printer = None

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
    return jsonify({"message": "Order received!", "order": data})
    print(data)
    print(user_agent)
    # filter for food and drinks
    items_food = [item for item in data['orderedItems'] if item['type'] == 'food']
    items_drinks = [item for item in data['orderedItems'] if item['type'] == 'drink']
    printer_food.print_order(data['tableNumber'], items_food, comment=data['comment'])
    printer_drinks.print_order(data['tableNumber'], items_drinks, comment=data['comment'])
    return jsonify({"message": "Order received!", "order": data})

def main():
    app.run(debug=False, host='0.0.0.0')

if __name__ == "__main__":
    main()
