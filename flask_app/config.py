"""
Configuration settings for the Flask ordering system.
"""

class Config:
    """Application configuration class"""
    
    # Flask settings
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Printer settings
    MOCK_PRINTER = True
    PRINTER_IP = "192.168.0.24"
    LOGO_PATH = '../resources/Rucksackberger_solo.png'
    
    # File paths
    MENU_PATH = "../resources/menu.json"
    DATABASE_PATH = "orders.db"
    CSV_FALLBACK_PATH = "data.csv"
    
    # Order processing settings
    ORDER_QUEUE_TIMEOUT = 1.0
    DEFAULT_ORDER_LIMIT = 50
    
    @classmethod
    def get_printer_config(cls):
        """Get printer configuration"""
        return {
            'mock': cls.MOCK_PRINTER,
            'ip': cls.PRINTER_IP,
            'logo_path': cls.LOGO_PATH
        }
