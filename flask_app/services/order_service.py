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


from models import Order

class OrderService:
    """Service for managing order processing and data operations"""

    def __init__(self):
        """Initialize order service"""
        self.log = logging.getLogger(__name__)
        self.log.info("Initializing order service")

        self.order_logger = OrderLogger(Config.DATABASE_PATH)
        self.printer_service = PrinterService()
        self.printer_order_queue = Queue()
        self.dashboard_order_queue = Queue()
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
                    self.dashboard_order_queue.put(order)
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
                self.log.error(f"Error processing order: {e}")


    def process_order(self, order_data, user_agent=None):
        """Process a new order - save to database and add to print queue"""
        try:
            order = order_data if isinstance(order_data, Order) else Order.from_dict(order_data)
            if user_agent:
                order.user_agent = user_agent

            self.log.info(f"Processing order for table {order.table_number} with {len(order.items)} items")
            
            # Save order to database
            order_id = self.order_logger.save_order(order, user_agent)
            order.id = order_id
            self.log.info(f"Order saved to database with ID: {order_id}")

            # Add to queues
            self.printer_order_queue.put(order)
            self.dashboard_order_queue.put(order)
            self.log.info(f"Order added to print queue for table {order.table_number}")

            return order_id
        except Exception as e:
            self.log.error(f"Error saving order: {e}")
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
        Get recent orders for dashboard display with optional filtering
        Args:
            filter (dict): Dictionary containing 'key' and 'value' to filter by
        Returns:
            list: Filtered list of order dicts
        """
        orders_in_queue = list(self.dashboard_order_queue.queue)
        filtered_orders = []

        for item in orders_in_queue:
            order = item if isinstance(item, Order) else Order.from_dict(item)

            if not filter or order.has_item_type(filter.get('value')):
                filtered_orders.append(order.to_dict())

        return filtered_orders

    def remove_order_from_queue(self, order_timestamp):
        """Remove an order from the dashboard queue"""
        for item in list(self.dashboard_order_queue.queue):
            ts = item.timestamp if isinstance(item, Order) else item.get('timestamp')
            if ts == order_timestamp:
                self.dashboard_order_queue.queue.remove(item)
                break


    def update_order_status(self, order_id, status):
        """Update the status of an order"""
        return self.order_logger.update_order_status(order_id, status)

    def get_sales_summary(self, date_from=None, date_to=None):
        """Get sales analytics"""
        ret = self.order_logger.get_sales_summary(date_from, date_to)
        print(ret)
        return ret

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
