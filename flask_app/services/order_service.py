"""
Order processing service for handling order business logic.
"""
import datetime
from datetime import datetime
from queue import Queue
from threading import Thread
from services.order_logger import OrderLogger
from services.printer_service import PrinterService
from utils.file_utils import save_order_csv
from config import Config
import logging
import time

# Add Pydantic imports
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from models import Order

class MenuItem(BaseModel):
    """Pydantic model for menu items"""
    name: str
    price: float = Field(gt=0)
    category: Optional[str] = None
    quantity: int = Field(default=1, ge=1)

class OrderValidation(BaseModel):
    """Pydantic model for order validation"""
    table_number: int = Field(gt=0)
    items: List[MenuItem]
    timestamp: Optional[datetime] = None
    user_agent: Optional[str] = None
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        return v

class OrderService:
    """Service for managing order processing and data operations"""

    def __init__(self):
        """Initialize order service"""
        self.log = logging.getLogger(__name__)
        self.log.info("Initializing order service")

        self.order_logger = OrderLogger(Config.DATABASE_PATH)
        self.printer_service = PrinterService()
        self.printer_order_queue = Queue()

        self._start_order_processing_thread()
        self._recover_pending_orders()

    def _recover_pending_orders(self):
        """Recover unprinted orders from SQLite database on startup"""
        try:
            pending_orders = self.order_logger.get_pending_orders()
            if pending_orders:
                self.log.info(f"Recovered {len(pending_orders)} unprinted order(s) from database for processing.")
                for order in pending_orders:
                    self.printer_order_queue.put(order)

            else:
                self.log.info("No unprinted orders found in database on startup.")
        except Exception as e:
            self.log.error(f"Error recovering pending orders from DB: {e}")

    def _start_order_processing_thread(self):
        """Start background thread for processing orders"""
        self.order_thread = Thread(target=self._process_orders, daemon=True)
        self.order_thread.start()

    def _process_orders(self):
        """Background process for handling order queue"""
        while True:
            try:
                # Wait until an order is available
                order_item = self.printer_order_queue.get(block=True)
                order = order_item if isinstance(order_item, Order) else Order.from_dict(order_item)

                if not self.printer_service.are_printers_available():
                    self.log.warning("Printer is not available, please check the printer. Re-queuing order. Timeout for 10 seconds")
                    self.printer_order_queue.put(order)
                    time.sleep(10)
                    continue

                success = self.printer_service.print_order(order)

                if success:
                    self.printer_order_queue.task_done()
                    # Update status in database to 'printed'
                    if order.id:
                        self.order_logger.update_order_status(order.id, 'printed')
                        order.status = 'printed'
                        self.log.info(f"Order #{order.id} status updated to 'printed' in database.")
                else:
                    self.log.warning("Failed to print order, will retry...")
                    time.sleep(10)  # Warten Sie 10 Sekunden vor dem erneuten Einfügen
                    self.printer_order_queue.put(order)

            except Exception as e:
                self.log.exception("Error processing order from queue")

    def process_order(self, order_data, user_agent=None):
        """Process a new order - save to database and add to print queue"""
        try:
            # Validate order data using Pydantic
            if isinstance(order_data, dict):
                validated_order = OrderValidation(**order_data)
                # Convert back to dict for further processing
                order_dict = validated_order.dict()
                order = Order.from_dict(order_dict)
            else:
                # If it's already an Order object, validate it
                order = order_data

            if user_agent:
                order.user_agent = user_agent

            self.log.info(f"Processing order for table {order.table_number} with {len(order.items)} items")
            
            # Save order to database
            order_id = self.order_logger.save_order(order, user_agent)
            order.id = order_id
            self.log.info(f"Order saved to database with ID: {order_id}")

            # Add to print queue — dashboard state is read directly from the DB
            self.printer_order_queue.put(order)
            self.log.info(f"Order added to print queue for table {order.table_number}")

            return order_id
        except Exception as e:
            self.log.exception("Error saving order, falling back to CSV")
            # Fallback to CSV if SQLite fails
            raw_data = order_data.to_dict() if hasattr(order_data, 'to_dict') else order_data
            return save_order_csv(Config.CSV_FALLBACK_PATH, raw_data, user_agent)

    def get_orders(self, table_number=None, limit=None):
        """Get orders with optional filtering"""
        if limit is None:
            limit = Config.DEFAULT_ORDER_LIMIT
        if table_number:
            return self.order_logger.get_orders_by_table(table_number, limit)
        else:
            return self.order_logger.get_recent_orders(limit)

    def get_order_details(self, order_id):
        """Get detailed information about a specific order"""
        return self.order_logger.get_order(order_id)

    def get_dashboard_orders(self, filter=None):
        """
        Get active (non-completed) orders for dashboard display, sourced directly
        from the database — this is the single source of truth, consistent across
        worker processes and durable across restarts.
        Args:
            filter (dict): Dictionary containing 'key' and 'value' to filter by item type
        Returns:
            list: Filtered list of order dicts
        """
        item_type = filter.get('value') if filter else None
        orders = self.order_logger.get_unprocessed_orders(item_type)
        self.log.info(f"Retrieved {len(orders)} active order(s) from database for dashboard.")
        return [order.to_dict() for order in orders]

    def complete_order(self, order_id):
        """Mark an order as completed (persisted in the database)"""
        return self.order_logger.update_order_status(order_id, 'completed')
    
    def set_order_processed(self, order_id, item_type):
        """Mark the food or drink portion of an order as processed (persisted in the database)"""
        return self.order_logger.update_type_processed_status(order_id, item_type)

    def update_order_status(self, order_id, status):
        """Update the status of an order"""
        return self.order_logger.update_order_status(order_id, status)

    def get_sales_summary(self, date_from=None, date_to=None):
        """Get sales analytics"""
        summary = self.order_logger.get_sales_summary(date_from, date_to)
        self.log.debug(f"Sales summary ({date_from} - {date_to}): {summary}")
        return summary

    def get_popular_items(self, limit=10):
        """Get most popular menu items"""
        return self.order_logger.get_popular_items(limit)

    def export_orders(self, date_from=None, date_to=None):
        """Export orders to CSV"""
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.order_logger.export_to_csv(filename, date_from, date_to)
        return filename

    def get_queue_status(self):
        """Get current order queue status"""
        return {
            'pending_orders': self.printer_order_queue.qsize(),
            'printer_status': self.printer_service.get_printer_status()
        }
