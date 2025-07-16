import pytest
import os
import tempfile
from datetime import datetime, timedelta
from order_logger import OrderLogger


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    logger = OrderLogger(db_path)
    yield logger
    
    # Cleanup - try to close any open connections first
    try:
        # Force close any remaining connections
        import gc
        gc.collect()
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        # On Windows, sometimes the file is still locked
        # This is acceptable for tests
        pass


def test_order_logger_initialization(temp_db):
    """Test that the OrderLogger initializes correctly"""
    assert temp_db.db_path is not None
    assert os.path.exists(temp_db.db_path)


def test_save_order(temp_db):
    """Test saving an order to the database"""
    test_order = {
        'tableNumber': 5,
        'orderedItems': [
            {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 2},
            {'id': 18, 'name': 'Schweinekeule mit Brot', 'price': 8.0, 'type': 'food', 'quantity': 1}
        ],
        'comment': 'Test order'
    }
    
    order_id = temp_db.save_order(test_order, 'TestAgent/1.0')
    
    assert order_id is not None
    assert isinstance(order_id, int)
    assert order_id > 0


def test_get_order(temp_db):
    """Test retrieving an order from the database"""
    test_order = {
        'tableNumber': 3,
        'orderedItems': [
            {'id': 11, 'name': 'Coca-Cola', 'price': 3.0, 'type': 'drink', 'quantity': 1}
        ],
        'comment': 'Get order test'
    }
    
    order_id = temp_db.save_order(test_order, 'TestAgent/1.0')
    retrieved_order = temp_db.get_order(order_id)
    
    assert retrieved_order is not None
    assert retrieved_order['order']['table_number'] == 3
    assert retrieved_order['order']['comment'] == 'Get order test'
    assert len(retrieved_order['items']) == 1
    assert retrieved_order['items'][0]['item_name'] == 'Coca-Cola'


def test_get_nonexistent_order(temp_db):
    """Test retrieving a non-existent order"""
    result = temp_db.get_order(999)
    assert result is None


def test_get_orders_by_table(temp_db):
    """Test getting orders for a specific table"""
    # Add orders for different tables
    order1 = {
        'tableNumber': 1,
        'orderedItems': [{'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 1}],
        'comment': 'Table 1 order 1'
    }
    
    order2 = {
        'tableNumber': 1,
        'orderedItems': [{'id': 2, 'name': 'Radler', 'price': 3.5, 'type': 'drink', 'quantity': 1}],
        'comment': 'Table 1 order 2'
    }
    
    order3 = {
        'tableNumber': 2,
        'orderedItems': [{'id': 3, 'name': 'Weizen', 'price': 3.5, 'type': 'drink', 'quantity': 1}],
        'comment': 'Table 2 order'
    }
    
    temp_db.save_order(order1)
    temp_db.save_order(order2)
    temp_db.save_order(order3)
    
    table1_orders = temp_db.get_orders_by_table(1)
    table2_orders = temp_db.get_orders_by_table(2)
    
    assert len(table1_orders) == 2
    assert len(table2_orders) == 1
    assert table1_orders[0]['table_number'] == 1
    assert table2_orders[0]['table_number'] == 2


def test_update_order_status(temp_db):
    """Test updating order status"""
    test_order = {
        'tableNumber': 4,
        'orderedItems': [{'id': 1, 'name': 'Test Item', 'price': 5.0, 'type': 'food', 'quantity': 1}],
        'comment': 'Status test'
    }
    
    order_id = temp_db.save_order(test_order)
    
    # Update status
    success = temp_db.update_order_status(order_id, 'completed')
    assert success is True
    
    # Verify status was updated
    order = temp_db.get_order(order_id)
    assert order['order']['status'] == 'completed'
    
    # Test updating non-existent order
    success = temp_db.update_order_status(999, 'completed')
    assert success is False


def test_get_recent_orders(temp_db):
    """Test getting recent orders"""
    # Add multiple orders
    for i in range(5):
        order = {
            'tableNumber': i + 1,
            'orderedItems': [{'id': i, 'name': f'Item {i}', 'price': 10.0, 'type': 'food', 'quantity': 1}],
            'comment': f'Order {i}'
        }
        temp_db.save_order(order)
    
    recent_orders = temp_db.get_recent_orders(3)
    
    assert len(recent_orders) == 3
    # Should be ordered by most recent first (last table number should be higher)
    assert recent_orders[0]['table_number'] >= recent_orders[1]['table_number']


def test_sales_summary(temp_db):
    """Test sales summary functionality"""
    # Add orders with different prices
    orders = [
        {
            'tableNumber': 1,
            'orderedItems': [{'id': 1, 'name': 'Item 1', 'price': 10.0, 'type': 'food', 'quantity': 1}],
            'comment': 'Order 1'
        },
        {
            'tableNumber': 2,
            'orderedItems': [
                {'id': 2, 'name': 'Item 2', 'price': 5.0, 'type': 'drink', 'quantity': 2},
                {'id': 3, 'name': 'Item 3', 'price': 15.0, 'type': 'food', 'quantity': 1}
            ],
            'comment': 'Order 2'
        }
    ]
    
    for order in orders:
        temp_db.save_order(order)
    
    summary = temp_db.get_sales_summary()
    
    assert summary['total_orders'] == 2
    assert summary['total_revenue'] == 35.0  # 10 + (5*2) + 15
    assert summary['average_order_value'] == 17.5
    assert summary['min_order_value'] == 10.0
    assert summary['max_order_value'] == 25.0


def test_popular_items(temp_db):
    """Test popular items functionality"""
    # Add orders with repeated items
    orders = [
        {
            'tableNumber': 1,
            'orderedItems': [
                {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 2},
                {'id': 2, 'name': 'Pizza', 'price': 12.0, 'type': 'food', 'quantity': 1}
            ],
            'comment': 'Order 1'
        },
        {
            'tableNumber': 2,
            'orderedItems': [
                {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 1},
                {'id': 3, 'name': 'Salad', 'price': 8.0, 'type': 'food', 'quantity': 1}
            ],
            'comment': 'Order 2'
        }
    ]
    
    for order in orders:
        temp_db.save_order(order)
    
    popular_items = temp_db.get_popular_items()
    
    assert len(popular_items) > 0
    # Pils should be most popular (quantity 3 total)
    assert popular_items[0]['item_name'] == 'Pils'
    assert popular_items[0]['total_quantity'] == 3


def test_export_to_csv(temp_db):
    """Test CSV export functionality"""
    # Add a test order
    test_order = {
        'tableNumber': 1,
        'orderedItems': [{'id': 1, 'name': 'Test Item', 'price': 5.0, 'type': 'food', 'quantity': 1}],
        'comment': 'Export test'
    }
    
    temp_db.save_order(test_order)
    
    # Export to CSV
    csv_file = 'test_export.csv'
    temp_db.export_to_csv(csv_file)
    
    # Check file was created
    assert os.path.exists(csv_file)
    
    # Check file content
    with open(csv_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'Test Item' in content
        assert 'Export test' in content
    
    # Cleanup
    os.unlink(csv_file)


def test_total_price_calculation(temp_db):
    """Test that total price is calculated correctly"""
    test_order = {
        'tableNumber': 1,
        'orderedItems': [
            {'id': 1, 'name': 'Item 1', 'price': 10.0, 'type': 'food', 'quantity': 2},  # 20.0
            {'id': 2, 'name': 'Item 2', 'price': 5.0, 'type': 'drink', 'quantity': 3},  # 15.0
            {'id': 3, 'name': 'Item 3', 'price': 7.5, 'type': 'food', 'quantity': 1}   # 7.5
        ],
        'comment': 'Price calculation test'
    }
    
    order_id = temp_db.save_order(test_order)
    order = temp_db.get_order(order_id)
    
    expected_total = (10.0 * 2) + (5.0 * 3) + (7.5 * 1)  # 42.5
    assert order['order']['total_price'] == expected_total


# Integration tests for database schema
def test_database_schema(temp_db):
    """Test that database tables are created correctly"""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check orders table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        assert cursor.fetchone() is not None
        
        # Check order_items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_items'")
        assert cursor.fetchone() is not None
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_orders_timestamp'")
        assert cursor.fetchone() is not None
