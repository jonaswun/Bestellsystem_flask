"""
Menu-related routes for the ordering system.
"""
from flask import Blueprint, jsonify, make_response
from utils.file_utils import load_menu

menu_bp = Blueprint('menu', __name__)

@menu_bp.route("/menu", methods=["GET"])
def get_menu():
    """Get the menu items"""
    menu = load_menu()
    response = make_response(jsonify(menu))
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response
