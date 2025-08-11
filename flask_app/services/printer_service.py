"""
Printer management service for handling multiple printers.
"""
from services.Printer import Printer
from services.MockPrinter import MockPrinter
from config import Config

class PrinterService:
    """Service for managing food and drink printers"""

    def __init__(self):
        """Initialize printer service with configuration"""
        self.config = Config.get_printer_config()
        self._initialize_printers()

    def _initialize_printers(self):
        """Initialize the printers based on configuration"""
        if self.config['mock']:
            self.printer_food = MockPrinter()
            self.printer_drinks = MockPrinter()
        else:
            self.printer_food = Printer(
                self.config['ip'], 
                logo_path=self.config['logo_path']
            )
            # Using same printer for both food and drinks for now
            self.printer_drinks = self.printer_food

    def are_printers_available(self):
        """Check if both printers are available"""
        return (self.printer_food.is_available() and
                self.printer_drinks.is_available())

    def print_order(self, table_number, items, comment=""):
        """Print order to appropriate printers based on item types"""
        try:
            # Separate items by type
            items_food = [item for item in items if item.get('type') == 'food']
            items_drinks = [item for item in items if item.get('type') == 'drink']

            # Print to appropriate printers
            if items_food:
                self.printer_food.print_order(table_number, items_food, comment=comment)

            if items_drinks:
                self.printer_drinks.print_order(table_number, items_drinks, comment=comment)

            return True
        except Exception as e:
            print(f"Error printing order: {e}")
            return False

    def get_printer_status(self):
        """Get status of both printers"""
        return {
            'food_printer': {
                'available': self.printer_food.is_available(),
                'type': 'mock' if self.config['mock'] else 'physical'
            },
            'drinks_printer': {
                'available': self.printer_drinks.is_available(),
                'type': 'mock' if self.config['mock'] else 'physical'
            }
        }
