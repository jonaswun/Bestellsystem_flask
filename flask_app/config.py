"""
Configuration settings for the Flask ordering system.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Application configuration class"""
    
    # Flask settings
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Printer settings
    MOCK_PRINTER = False
    DRINKS_PRINTER_IP = "192.168.0.24"
    FOOD_PRINTER_IP = "192.168.0.24"
    LOGO_PATH = str(BASE_DIR / "resources" / "Rucksackberger_solo.png")
    
    # File paths
    MENU_PATH = str(BASE_DIR / "resources" / "menu.json")
    DATABASE_PATH = str(BASE_DIR / "data" / "orders.db")
    CSV_FALLBACK_PATH = str(BASE_DIR / "data.csv")
    
    # Order processing settings
    ORDER_QUEUE_TIMEOUT = 1.0
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
