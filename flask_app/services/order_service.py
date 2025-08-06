"""
Order processing service for handling order business logic.
"""
from datetime import datetime
from queue import Queue
from threading import Thread
from services.order_logger import OrderLogger
from services.printer_service import PrinterService
from utils.file_utils import save_order_csv
from config import Config


class OrderService:
    """Service for managing order processing and data operations"""
    
    def __init__(self):
        """Initialize order service"""
        self.order_logger = OrderLogger(Config.DATABASE_PATH)
        self.printer_service = PrinterService()
        self.order_queue = Queue()
        self._start_order_processing_thread()
    
    def _start_order_processing_thread(self):
        """Start background thread for processing orders"""
        self.order_thread = Thread(target=self._process_orders, daemon=True)
        self.order_thread.start()
    
    def _process_orders(self):
        """Background process for handling order queue"""
        while True:
            try:
                # Check if queue is empty
                if self.order_queue.empty():
                    continue
                
                # Peek at the first order without removing it
                order = self.order_queue.queue[0]
                
                # Check if printers are available
                if not self.printer_service.are_printers_available():
                    print("Printers not available, skipping order processing.")
                    continue
                
                # Process the order
                success = self.printer_service.print_order(
                    order['tableNumber'], 
                    order['orderedItems'], 
                    comment=order.get('comment', '')
                )
                
                if success:
                    # Remove the order from queue after successful processing
                    self.order_queue.get()
                    self.order_queue.task_done()
                    print(f"Order for table {order['tableNumber']} processed successfully")
                else:
                    print("Failed to print order, will retry...")
                    
            except Exception as e:
                print(f"Error processing order: {e}")
                # Remove problematic order to prevent infinite loop
                if not self.order_queue.empty():
                    self.order_queue.get()
                    self.order_queue.task_done()
    
    def process_order(self, data, user_agent=None, user_info=None):
        """
        Process a new order with user information
        
        Args:
            data (dict): Order data
            user_agent (str): User agent string
            user_info (dict): User information including user_id, username, role
            
        Returns:
            int: Order ID
        """
        # Log order to database with user information
        order_id = self.order_logger.save_order(data, user_agent, user_info)
        
        # Add order to processing queue with user info
        order_data = {
            'order_id': order_id,
            'tableNumber': data.get('tableNumber'),
            'orderedItems': data.get('orderedItems', []),
            'comment': data.get('comment', ''),
            'user_info': user_info
        }
        
        # Add to queue for background processing
        self.order_queue.put(order_data)
        
        # Save as CSV fallback
        try:
            save_order_csv(data, Config.CSV_FALLBACK_PATH, user_info)
        except Exception as e:
            print(f"Failed to save CSV fallback: {e}")
        
        return order_id
    
    def get_orders_by_user(self, user_id, limit=50):
        """
        Get orders for a specific user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of orders to return
            
        Returns:
            list: List of orders for the user
        """
        return self.order_logger.get_orders_by_user(user_id, limit)
    
    def get_orders(self, table_number=None, limit=50):
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
    
    def update_order_status(self, order_id, status):
        """Update the status of an order"""
        return self.order_logger.update_order_status(order_id, status)
    
    def get_sales_summary(self, date_from=None, date_to=None):
        """Get sales analytics"""
        return self.order_logger.get_sales_summary(date_from, date_to)
    
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
            'pending_orders': self.order_queue.qsize(),
            'printer_status': self.printer_service.get_printer_status()
        }
    
    def get_user_activity_stats(self):
        """Get user activity analytics"""
        return self.order_logger.get_user_activity_stats()
    
    def get_user_order_stats(self, user_id):
        """Get order statistics for a specific user"""
        return self.order_logger.get_user_order_stats(user_id)
