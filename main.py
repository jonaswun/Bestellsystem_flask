import json
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from Printer import Printer

app = Flask(__name__)
CORS(app)

printer = None

printer = Printer("192.168.0.24", logo_path='Rucksackberger_solo.png')

# Load menu from JSON file
with open("menu.json", encoding="utf-8") as f:
    menu = json.load(f)
    print(menu)

@app.route("/menu", methods=["GET"])
def get_menu():
    response = make_response(jsonify(menu))
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

@app.route("/order", methods=["POST"])
def place_order():
    data = request.json
    printer.print_order(data['tableNumber'], data['orderedItems'], comment=data['comment'])
    return jsonify({"message": "Order received!", "order": data})

def main():
    app.run(debug=False, host='0.0.0.0')

if __name__ == "__main__":
    main()
