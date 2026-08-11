import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path
from config import Config


class OrderLogger:
    """SQLite-based order logging system"""

    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()


    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
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
                    processed BOOLEAN DEFAULT FALSE,
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

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_status
                ON orders (status)
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
            data (Order or dict): Order instance or dict containing order details
            user_agent (str): User agent string from request headers

        Returns:
            int: The ID of the created order
        """
        from models import Order
        order = data if isinstance(data, Order) else Order.from_dict(data)

        timestamp = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert order
            cursor.execute('''
                INSERT INTO orders (timestamp, table_number, user_agent, comment, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                timestamp,
                order.table_number,
                user_agent or order.user_agent,
                order.comment,
                order.total_price
            ))

            order_id = cursor.lastrowid
            order.id = order_id

            # Insert order items
            for item in order.items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, item_id, item_name, item_type, price, quantity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    item.id,
                    item.name,
                    item.type,
                    item.price,
                    item.quantity
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
            cursor.execute(
                'SELECT * FROM order_items WHERE order_id = ?', (order_id,))
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

    def update_order_processed_status(self, order_id, processed=True):
        """Update the processed status of an order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders
                SET processed = ?
                WHERE id = ?
            ''', (processed, order_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_unprocessed_orders(self, item_type=None):
        """Get all unprocessed orders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if item_type:
                cursor.execute('''
                    SELECT * FROM orders
                    WHERE processed = FALSE AND id IN (
                        SELECT order_id FROM order_items WHERE item_type = ?
                    )
                    ORDER BY created_at ASC
                ''', (item_type,))
            else:
                cursor.execute('''
                    SELECT * FROM orders
                    WHERE processed = FALSE
                    ORDER BY created_at ASC
                ''')
            # sqlite3's cursor.rowcount is -1 for SELECT statements; fetch once
            rows = cursor.fetchall()
            count = len(rows)
            print(f"Retrieved {count} unprocessed order(s) from database.")
            # Return Order objects (with items) so callers can call .to_dict()
            return [self._row_to_order(row, cursor) for row in rows]

    def _row_to_order(self, order_row, cursor):
        """Build an Order (with items) from an `orders` row using the given cursor"""
        from models import Order
        order_dict = dict(order_row)
        cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order_dict['id'],))
        items_rows = cursor.fetchall()

        items = []
        for item_row in items_rows:
            ir = dict(item_row)
            items.append({
                'id': ir.get('item_id'),
                'name': ir.get('item_name'),
                'type': ir.get('item_type'),
                'price': ir.get('price'),
                'quantity': ir.get('quantity'),
            })

        return Order.from_dict({
            'id': order_dict['id'],
            'table_number': order_dict['table_number'],
            'comment': order_dict.get('comment', ''),
            'timestamp': order_dict.get('timestamp'),
            'status': order_dict.get('status', 'pending'),
            'processed': order_dict.get('processed', False),
            'created_at': order_dict.get('created_at'),
            'user_agent': order_dict.get('user_agent'),
            'orderedItems': items
        })

    def get_pending_orders(self):
        """Get all pending (unprinted) orders from DB with their items for recovery"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM orders
                WHERE status = 'pending'
                ORDER BY id ASC
            ''')
            rows = cursor.fetchall()
            return [self._row_to_order(row, cursor) for row in rows]

    def get_active_orders(self, item_type=None):
        """
        Get all non-completed orders (with items) for dashboard/kitchen display.
        This is the single source of truth for "what's still open" — no in-memory
        state is kept, so this reflects every worker process consistently.

        Args:
            item_type (str): Optional item type ('food'/'drink') an order must
                contain at least one of; the full order (all items) is still returned.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if item_type:
                cursor.execute('''
                    SELECT DISTINCT o.*
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.status != 'completed' AND oi.item_type = ?
                    ORDER BY o.created_at ASC
                ''', (item_type,))
            else:
                cursor.execute('''
                    SELECT * FROM orders
                    WHERE status != 'completed'
                    ORDER BY created_at ASC
                ''')
            rows = cursor.fetchall()
            return [self._row_to_order(row, cursor) for row in rows]


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
                    o.comment, o.total_price, o.status, o.processed,
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
                    'comment', 'total_price', 'status', 'processed',
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
