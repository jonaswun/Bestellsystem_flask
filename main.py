import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from Printer import Printer

app = Flask(__name__)
CORS(app)

printer = None

printer = Printer("192.168.0.24", logo_path='Rucksackberger_solo.png')

# Load menu from JSON file
with open("menu.json") as f:
    menu = json.load(f)
    print(menu)

@app.route("/menu", methods=["GET"])
def get_menu():
    return jsonify(menu)

@app.route("/order", methods=["POST"])
def place_order():
    data = request.json
    printer.print_order(data['orderedItems'])

    return jsonify({"message": "Order received!", "order": data})

def main():
    print("hallo")

    app.run(debug=False)
    
if __name__ == "__main__":
    main()
