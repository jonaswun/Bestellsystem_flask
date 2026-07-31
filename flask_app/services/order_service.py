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

    def _start_order_processing_thread(self):
        """Start background thread for processing orders"""
        self.order_thread = Thread(target=self._process_orders, daemon=True)
        self.order_thread.start()

    def _process_orders(self):
        """Background process for handling order queue"""
        while True:
            try:
                # Wait until an order is available
                order = self.printer_order_queue.get(block=True)

                if not self.printer_service.are_printers_available():
                    self.log.warning("Printer is not available, please check the printer. Re-queuing order. Timeout for 10 seconds")
                    self.printer_order_queue.put(order)
                    time.sleep(10)
                    continue
                
                success = self.printer_service.print_order(
                    order['tableNumber'],
                    order['orderedItems'],
                    comment=order.get('comment', ''),
                    timestamp=order.get('timestamp', None)
                )

                if success:
                    self.printer_order_queue.task_done()
                else:
                    self.log.warning("Failed to print order, will retry...")
                    self.printer_order_queue.put(order)

            except Exception as e:
                self.log.error(f"Error processing order: {e}")
                self.printer_order_queue.put(order)

    def process_order(self, order_data, user_agent):
        """Process a new order - save to database and add to print queue"""
        try:

            self.log.info(f"Processing order: {order_data}")    
            # Save order to database
            order_id = self.order_logger.save_order(order_data, user_agent)
            self.log.info(f"Order saved to database with ID: {order_id}")

            # Add to print queue
            self.printer_order_queue.put(order_data)
            self.dashboard_order_queue.put(order_data)
            self.log.info(f"Order added to print queue for table {order_data['tableNumber']}")

            return order_id
        except Exception as e:
            self.log.error(f"Error saving order: {e}")
            # Fallback to CSV if SQLite fails
            return save_order_csv(Config.CSV_FALLBACK_PATH, order_data, user_agent)

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
            list: Filtered list of orders
        """
        # Get all orders from queue
        orders = list(self.dashboard_order_queue.queue)
        print(f"All orders before filtering: {orders}")

        # If no filter specified, return all orders
        if not filter:
            return orders

        # Filter orders that contain items matching the filter value
        filtered_orders = []
        for order in orders:
            # Check if any ordered item matches the filter
            has_matching_item = any(
                item.get('type') == filter['value']
                for item in order.get('orderedItems', [])
            )

            if has_matching_item:
                filtered_orders.append(order)

        print(f"Filtered orders: {filtered_orders}")
        return filtered_orders

    def remove_order_from_queue(self, order_timestamp):
        """Remove an order from the dashboard queue"""
        # find the order which has the matching timestamp
        for order in list(self.dashboard_order_queue.queue):
            if order.get('timestamp') == order_timestamp:
                self.dashboard_order_queue.queue.remove(order)
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
