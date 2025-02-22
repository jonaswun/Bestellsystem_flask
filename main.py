from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

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
    return jsonify({"message": "Order received!", "order": data})

if __name__ == "__main__":
    app.run(debug=True)
