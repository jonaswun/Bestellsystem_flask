"""
Configuration settings for the Flask ordering system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Loads repo-root .env (shared with docker-compose); real env vars still win.
load_dotenv(BASE_DIR.parent / ".env")

class Config:
    """Application configuration class"""
    
    # Flask settings
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5000

    # Logging settings (override via LOG_LEVEL / LOG_DIR env vars)
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / "data" / "logs"))

    # Printer settings (override via FOOD_PRINTER_IP / DRINKS_PRINTER_IP env vars)
    MOCK_PRINTER = False
    MINIMAL_PRINTER_OUTPUT = os.getenv('MINIMAL_PRINTER_OUTPUT', 'False').lower() in ('1', 'true', 'yes')
    DRINKS_PRINTER_IP = os.getenv('DRINKS_PRINTER_IP', '')
    FOOD_PRINTER_IP = os.getenv('FOOD_PRINTER_IP', '')
    LOGO_PATH = str(BASE_DIR / "resources" / "Rucksackberger_solo.png")

    # File paths
    MENU_PATH = str(BASE_DIR / "resources" / "menu.json")
    DATABASE_PATH = str(BASE_DIR / "data" / "orders.db")
    CSV_FALLBACK_PATH = str(BASE_DIR / "data.csv")

    # Order processing settings
    DEFAULT_ORDER_LIMIT = 50

    @classmethod
    def get_printer_config(cls):
        """Get printer configuration"""
        return {
            'mock': cls.MOCK_PRINTER,
            'ip_drinks': cls.DRINKS_PRINTER_IP,
            'ip_food': cls.FOOD_PRINTER_IP,
            'logo_path': cls.LOGO_PATH
        }
