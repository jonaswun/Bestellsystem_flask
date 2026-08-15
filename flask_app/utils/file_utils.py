"""
File utility functions for the ordering system.
"""
import json
import os
import csv
import logging
from datetime import datetime
from config import Config

log = logging.getLogger(__name__)

def load_menu():
    """Load menu from JSON file"""
    try:
        with open(Config.MENU_PATH, encoding="utf-8") as f:
            menu = json.load(f)
            log.info("Menu loaded successfully")
            return menu
    except FileNotFoundError:
        log.error(f"Menu file not found: {Config.MENU_PATH}")
        return {}
    except json.JSONDecodeError as e:
        log.error(f"Error parsing menu JSON: {e}")
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
            log.info(f"Order saved to CSV: {filename}")
            return None
    except Exception as e:
        log.exception(f"Error saving to CSV: {filename}")
        return None

