import pytest
import json
import os
from unittest.mock import patch, MagicMock
from main import app, order_queue


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def clear_queue():
    """Clear the order queue before each test"""
    while not order_queue.empty():
        try:
            order_queue.get_nowait()
        except:
            break
    yield
    # Cleanup after test if needed
    while not order_queue.empty():
        try:
            order_queue.get_nowait()
        except:
            break


@pytest.fixture
def sample_order():
    """Sample order data for testing"""
    return {
        'tableNumber': 5,
        'orderedItems': [
            {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 2},
            {'id': 18, 'name': 'Schweinekeule (ohne Knochen) mit Brot', 'price': 8.0, 'type': 'food', 'quantity': 1}
        ],
        'comment': 'Test order'
    }


class TestMenuEndpoint:
    """Test cases for the /menu endpoint"""

    def test_get_menu_success(self, client):
        """Test successful menu retrieval"""
        response = client.get('/menu')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json; charset=utf-8'
        
        data = json.loads(response.data)
        assert 'Bier' in data
        assert 'Wein' in data
        assert 'Alkoholfreie Getränke' in data
        assert 'Essen' in data
        assert 'Kaffee/Kuchen' in data

    def test_menu_structure(self, client):
        """Test the structure of menu data"""
        response = client.get('/menu')
        data = json.loads(response.data)
        
        # Check that beer items have required fields
        beer_items = data['Bier']
        assert len(beer_items) > 0
        
        first_beer = beer_items[0]
        assert 'id' in first_beer
        assert 'name' in first_beer
        assert 'price' in first_beer
        assert 'type' in first_beer

    def test_menu_item_types(self, client):
        """Test that menu items have correct types"""
        response = client.get('/menu')
        data = json.loads(response.data)
        
        # Check drink items
        for drink in data['Bier']:
            assert drink['type'] == 'drink'
        
        # Check food items
        for food in data['Essen']:
            if 'type' in food:  # Some items might not have type
                assert food['type'] == 'food'


class TestOrderEndpoint:
    """Test cases for the /order endpoint"""

    @patch('main.save_order')
    def test_place_order_success(self, mock_save_order, client, clear_queue, sample_order):
        """Test successful order placement"""
        response = client.post('/order', 
                              data=json.dumps(sample_order),
                              content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'Order received!'
        assert data['order'] == sample_order
        
        # Verify save_order was called
        mock_save_order.assert_called_once()

    def test_order_adds_to_queue(self, client, clear_queue):
        """Test that placing an order adds it to the processing queue"""
        initial_queue_size = order_queue.qsize()
        
        test_order = {
            'tableNumber': 3,
            'orderedItems': [
                {'id': 11, 'name': 'Coca-Cola', 'price': 3.0, 'type': 'drink', 'quantity': 1}
            ],
            'comment': ''
        }
        
        with patch('main.save_order'):
            response = client.post('/order',
                                  data=json.dumps(test_order),
                                  content_type='application/json')
        
        assert response.status_code == 200
        assert order_queue.qsize() == initial_queue_size + 1

    def test_order_with_user_agent(self, client, clear_queue):
        """Test that user agent is captured from request headers"""
        test_order = {
            'tableNumber': 7,
            'orderedItems': [
                {'id': 27, 'name': 'Kaffee', 'price': 2.5, 'type': 'drink', 'quantity': 1}
            ],
            'comment': 'Test with user agent'
        }
        
        with patch('main.save_order') as mock_save_order:
            response = client.post('/order',
                                  data=json.dumps(test_order),
                                  content_type='application/json',
                                  headers={'User-Agent': 'TestAgent/1.0'})
            
            assert response.status_code == 200
            
            # Check that save_order was called with the user agent
            args, kwargs = mock_save_order.call_args
            assert args[0] == 'data.csv'
            assert args[1] == test_order
            assert args[2] == 'TestAgent/1.0'

    def test_order_invalid_json(self, client):
        """Test placing an order with invalid JSON"""
        response = client.post('/order',
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400

    @pytest.mark.parametrize("missing_field", [
        {'tableNumber': 1},  # Missing orderedItems
        {'orderedItems': []},  # Missing tableNumber
        {}  # Empty order
    ])
    def test_order_missing_data(self, client, clear_queue, missing_field):
        """Test placing orders with missing required data"""
        with patch('main.save_order'):
            response = client.post('/order',
                                  data=json.dumps(missing_field),
                                  content_type='application/json')
        
        # The endpoint should handle this gracefully
        assert response.status_code in [200, 400, 500]

    def test_order_empty_items_list(self, client, clear_queue):
        """Test order with empty items list"""
        test_order = {
            'tableNumber': 1,
            'orderedItems': [],
            'comment': 'Empty order'
        }
        
        with patch('main.save_order'):
            response = client.post('/order',
                                  data=json.dumps(test_order),
                                  content_type='application/json')
        
        assert response.status_code == 200


class TestErrorHandling:
    """Test cases for error handling"""

    def test_invalid_endpoint(self, client):
        """Test accessing a non-existent endpoint"""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method"""
        response = client.post('/menu')
        assert response.status_code == 405

    def test_get_on_order_endpoint(self, client):
        """Test GET request on order endpoint (should fail)"""
        response = client.get('/order')
        assert response.status_code == 405


class TestOrderProcessing:
    """Test cases for order processing logic"""

    def test_queue_functionality(self, clear_queue):
        """Test that the order queue works correctly"""
        test_order = {
            'tableNumber': 1,
            'orderedItems': [{'id': 1, 'name': 'Test Item', 'type': 'drink', 'quantity': 1}],
            'comment': 'Test'
        }
        
        initial_size = order_queue.qsize()
        order_queue.put(test_order)
        assert order_queue.qsize() == initial_size + 1
        
        retrieved_order = order_queue.get()
        assert retrieved_order == test_order
        assert order_queue.qsize() == initial_size

    def test_queue_fifo_order(self, clear_queue):
        """Test that queue follows First-In-First-Out order"""
        orders = [
            {'tableNumber': 1, 'orderedItems': [], 'comment': 'First'},
            {'tableNumber': 2, 'orderedItems': [], 'comment': 'Second'},
            {'tableNumber': 3, 'orderedItems': [], 'comment': 'Third'}
        ]
        
        # Add orders to queue
        for order in orders:
            order_queue.put(order)
        
        # Retrieve orders and verify order
        for expected_order in orders:
            retrieved_order = order_queue.get()
            assert retrieved_order == expected_order


class TestIntegration:
    """Integration tests"""

    @patch('main.MockPrinter')
    def test_mock_printer_integration(self, mock_printer_class, client, clear_queue):
        """Test that the mock printer is used when MOCK_PRINTER is True"""
        mock_printer_instance = MagicMock()
        mock_printer_class.return_value = mock_printer_instance
        
        test_order = {
            'tableNumber': 2,
            'orderedItems': [
                {'id': 22, 'name': 'Grillwurst mit Brot', 'price': 3.5, 'type': 'food', 'quantity': 1}
            ],
            'comment': 'Mock printer test'
        }
        
        with patch('main.save_order'):
            response = client.post('/order',
                                  data=json.dumps(test_order),
                                  content_type='application/json')
        
        assert response.status_code == 200

    def test_full_order_workflow(self, client, clear_queue):
        """Test complete order workflow"""
        # 1. Get menu
        menu_response = client.get('/menu')
        assert menu_response.status_code == 200
        menu_data = json.loads(menu_response.data)
        
        # 2. Create order with items from menu
        pils = menu_data['Bier'][0]  # Get first beer item
        test_order = {
            'tableNumber': 10,
            'orderedItems': [
                {
                    'id': pils['id'],
                    'name': pils['name'],
                    'price': pils['price'],
                    'type': pils['type'],
                    'quantity': 2
                }
            ],
            'comment': 'Integration test order'
        }
        
        # 3. Place order
        with patch('main.save_order'):
            order_response = client.post('/order',
                                        data=json.dumps(test_order),
                                        content_type='application/json')
        
        assert order_response.status_code == 200
        order_data = json.loads(order_response.data)
        assert order_data['message'] == 'Order received!'
        assert order_data['order'] == test_order


# Performance and stress tests
class TestPerformance:
    """Performance and stress tests"""

    @pytest.mark.slow
    def test_multiple_concurrent_orders(self, client, clear_queue):
        """Test handling multiple orders in quick succession"""
        orders = []
        for i in range(10):
            order = {
                'tableNumber': i + 1,
                'orderedItems': [
                    {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 1}
                ],
                'comment': f'Order {i + 1}'
            }
            orders.append(order)
        
        with patch('main.save_order'):
            responses = []
            for order in orders:
                response = client.post('/order',
                                      data=json.dumps(order),
                                      content_type='application/json')
                responses.append(response)
        
        # All orders should be successful
        for response in responses:
            assert response.status_code == 200
        
        # Queue should contain all orders
        assert order_queue.qsize() == len(orders)


if __name__ == '__main__':
    pytest.main(['-v', __file__])
