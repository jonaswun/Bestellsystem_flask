import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager


class OrderLogger:
    """SQLite-based order logging system"""
    
    def __init__(self, db_path='orders.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    table_number INTEGER NOT NULL,
                    user_agent TEXT,
                    comment TEXT,
                    total_price REAL,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create order_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # Create index for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_timestamp 
                ON orders (timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_table_number 
                ON orders (table_number)
            ''')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    def save_order(self, data, user_agent=None):
        """
        Save an order to the database
        
        Args:
            data (dict): Order data containing tableNumber, orderedItems, comment
            user_agent (str): User agent string from request headers
        
        Returns:
            int: The ID of the created order
        """
        timestamp = datetime.now().isoformat()
        
        # Calculate total price
        total_price = sum(
            item.get('price', 0) * item.get('quantity', 1) 
            for item in data.get('orderedItems', [])
        )
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert order
            cursor.execute('''
                INSERT INTO orders (timestamp, table_number, user_agent, comment, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                timestamp,
                data.get('tableNumber'),
                user_agent,
                data.get('comment', ''),
                total_price
            ))
            
            order_id = cursor.lastrowid
            
            # Insert order items
            for item in data.get('orderedItems', []):
                cursor.execute('''
                    INSERT INTO order_items (order_id, item_id, item_name, item_type, price, quantity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    item.get('id'),
                    item.get('name'),
                    item.get('type'),
                    item.get('price', 0),
                    item.get('quantity', 1)
                ))
            
            conn.commit()
            return order_id
    
    def get_order(self, order_id):
        """Get a specific order by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get order details
            cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            order = cursor.fetchone()
            
            if not order:
                return None
            
            # Get order items
            cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,))
            items = cursor.fetchall()
            
            return {
                'order': dict(order),
                'items': [dict(item) for item in items]
            }
    
    def get_orders_by_table(self, table_number, limit=10):
        """Get recent orders for a specific table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM orders 
                WHERE table_number = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (table_number, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_orders(self, limit=50):
        """Get recent orders across all tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, 
                       COUNT(oi.id) as item_count
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                GROUP BY o.id
                ORDER BY o.created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_order_status(self, order_id, status):
        """Update the status of an order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders 
                SET status = ? 
                WHERE id = ?
            ''', (status, order_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_sales_summary(self, date_from=None, date_to=None):
        """Get sales summary for a date range"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_price) as total_revenue,
                    AVG(total_price) as average_order_value,
                    MIN(total_price) as min_order_value,
                    MAX(total_price) as max_order_value
                FROM orders
                WHERE 1=1
            '''
            params = []
            
            if date_from:
                query += ' AND timestamp >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND timestamp <= ?'
                params.append(date_to)
            
            cursor.execute(query, params)
            return dict(cursor.fetchone())
    
    def get_popular_items(self, limit=10):
        """Get most popular menu items"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    item_name,
                    item_type,
                    SUM(quantity) as total_quantity,
                    COUNT(*) as order_count,
                    AVG(price) as avg_price
                FROM order_items
                GROUP BY item_id, item_name, item_type
                ORDER BY total_quantity DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def export_to_csv(self, filename, date_from=None, date_to=None):
        """Export orders to CSV file"""
        import csv
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    o.id, o.timestamp, o.table_number, o.user_agent, 
                    o.comment, o.total_price, o.status,
                    oi.item_name, oi.item_type, oi.price, oi.quantity
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE 1=1
            '''
            params = []
            
            if date_from:
                query += ' AND o.timestamp >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND o.timestamp <= ?'
                params.append(date_to)
            
            query += ' ORDER BY o.timestamp DESC'
            
            cursor.execute(query, params)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'order_id', 'timestamp', 'table_number', 'user_agent',
                    'comment', 'total_price', 'status',
                    'item_name', 'item_type', 'item_price', 'quantity'
                ])
                
                for row in cursor.fetchall():
                    writer.writerow(row)
    
    def cleanup_old_orders(self, days_old=30):
        """Remove orders older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First delete order items
            cursor.execute('''
                DELETE FROM order_items 
                WHERE order_id IN (
                    SELECT id FROM orders 
                    WHERE timestamp < ?
                )
            ''', (cutoff_date.isoformat(),))
            
            # Then delete orders
            cursor.execute('''
                DELETE FROM orders 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
            return cursor.rowcount
