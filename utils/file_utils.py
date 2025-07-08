"""
File utility functions for the ordering system.
"""
import json
import os
import csv
from datetime import datetime
from config import Config


def load_menu():
    """Load menu from JSON file"""
    try:
        with open(Config.MENU_PATH, encoding="utf-8") as f:
            menu = json.load(f)
            print("Menu loaded successfully")
            return menu
    except FileNotFoundError:
        print(f"Menu file not found: {Config.MENU_PATH}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing menu JSON: {e}")
        return {}


def save_order_csv(filename, data, user_type):
    """Fallback CSV logging method"""
    try:
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
            print(f"Order saved to CSV: {filename}")
            return None
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return None


def ensure_directory_exists(directory_path):
    """Ensure a directory exists, create if it doesn't"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")


def get_file_size(file_path):
    """Get file size in bytes, return 0 if file doesn't exist"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0
