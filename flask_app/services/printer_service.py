"""
Printer management service for handling multiple printers.
"""
import logging
from services.Printer import Printer
from services.MockPrinter import MockPrinter
from config import Config

from models import Order

log = logging.getLogger(__name__)

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
                self.config['ip_food'],
                logo_path=self.config['logo_path']
            )
            self.printer_drinks = Printer(
                self.config['ip_drinks'],
                logo_path=self.config['logo_path']
            )

    def are_printers_available(self):
        """Check if both printers are available"""
        return (self.printer_food.is_available() and
                self.printer_drinks.is_available())

    def print_order(self, order:Order):
        """Print order to appropriate printers based on item types"""
        try:
            if order.food_items:
                self.printer_food.print_order(order, order.food_items)

            if order.drink_items:
                self.printer_drinks.print_order(order, order.drink_items)

            return True
        except Exception as e:
            log.exception(f"Error printing order (order_id={getattr(order, 'id', None)})")
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
