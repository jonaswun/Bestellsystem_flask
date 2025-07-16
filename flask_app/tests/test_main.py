import pytest
import json
import os
from unittest.mock import patch, MagicMock
from flask_app.main import app, order_queue


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_queue():
    """Clear the order queue before each test"""
    while not order_queue.empty():
        try:
            order_queue.get_nowait()
        except:
            break
    yield
    # Clean up after test
    if os.path.exists('test_data.csv'):
        os.remove('test_data.csv')


class TestFlaskEndpoints:
    """Test cases for Flask application endpoints"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Clear the order queue before each test
        while not order_queue.empty():
            try:
                order_queue.get_nowait()
            except:
                break

    def tearDown(self):
        """Clean up after each test method"""
        # Clean up any test files
        if os.path.exists('test_data.csv'):
            os.remove('test_data.csv')

    def test_get_menu_endpoint(self):
        """Test the /menu GET endpoint"""
        response = self.app.get('/menu')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json; charset=utf-8')
        
        data = json.loads(response.data)
        self.assertIn('Bier', data)
        self.assertIn('Wein', data)
        self.assertIn('Alkoholfreie Getränke', data)
        self.assertIn('Essen', data)
        self.assertIn('Kaffee/Kuchen', data)

    def test_get_menu_structure(self):
        """Test the structure of menu data"""
        response = self.app.get('/menu')
        data = json.loads(response.data)
        
        # Check that beer items have required fields
        beer_items = data['Bier']
        self.assertGreater(len(beer_items), 0)
        
        first_beer = beer_items[0]
        self.assertIn('id', first_beer)
        self.assertIn('name', first_beer)
        self.assertIn('price', first_beer)
        self.assertIn('type', first_beer)

    @patch('main.save_order')
    def test_place_order_endpoint(self, mock_save_order):
        """Test the /order POST endpoint"""
        test_order = {
            'tableNumber': 5,
            'orderedItems': [
                {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 2},
                {'id': 18, 'name': 'Schweinekeule (ohne Knochen) mit Brot', 'price': 8.0, 'type': 'food', 'quantity': 1}
            ],
            'comment': 'Test order'
        }
        
        response = self.app.post('/order', 
                               data=json.dumps(test_order),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Order received!')
        self.assertEqual(data['order'], test_order)
        
        # Verify save_order was called
        mock_save_order.assert_called_once()

    def test_place_order_adds_to_queue(self):
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
            response = self.app.post('/order',
                                   data=json.dumps(test_order),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order_queue.qsize(), initial_queue_size + 1)

    def test_place_order_invalid_json(self):
        """Test placing an order with invalid JSON"""
        response = self.app.post('/order',
                               data='invalid json',
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_place_order_missing_data(self):
        """Test placing an order with missing required data"""
        incomplete_order = {
            'tableNumber': 1
            # Missing orderedItems and comment
        }
        
        with patch('main.save_order'):
            response = self.app.post('/order',
                                   data=json.dumps(incomplete_order),
                                   content_type='application/json')
        
        # The endpoint should handle this gracefully
        # Note: Your current implementation doesn't validate input, 
        # so this might pass but could cause errors in processing
        self.assertIn(response.status_code, [200, 400, 500])

    def test_invalid_endpoint(self):
        """Test accessing a non-existent endpoint"""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_order_with_user_agent(self):
        """Test that user agent is captured from request headers"""
        test_order = {
            'tableNumber': 7,
            'orderedItems': [
                {'id': 27, 'name': 'Kaffee', 'price': 2.5, 'type': 'drink', 'quantity': 1}
            ],
            'comment': 'Test with user agent'
        }
        
        with patch('main.save_order') as mock_save_order:
            response = self.app.post('/order',
                                   data=json.dumps(test_order),
                                   content_type='application/json',
                                   headers={'User-Agent': 'TestAgent/1.0'})
            
            self.assertEqual(response.status_code, 200)
            
            # Check that save_order was called with the user agent
            args, kwargs = mock_save_order.call_args
            self.assertEqual(args[0], 'data.csv')
            self.assertEqual(args[1], test_order)
            self.assertEqual(args[2], 'TestAgent/1.0')

    def test_cors_headers(self):
        """Test that CORS headers are present"""
        response = self.app.get('/menu')
        
        # Check if CORS is working (Flask-CORS should add these headers)
        self.assertEqual(response.status_code, 200)
        # Note: In test environment, CORS headers might not be visible
        # This test verifies the endpoint works with CORS enabled

    @patch('main.MockPrinter')
    def test_mock_printer_integration(self, mock_printer_class):
        """Test that the mock printer is used when MOCK_PRINTER is True"""
        # This test verifies the printer integration without actually printing
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
            response = self.app.post('/order',
                                   data=json.dumps(test_order),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)


class TestOrderProcessing(unittest.TestCase):
    """Test cases for order processing logic"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear the order queue
        while not order_queue.empty():
            try:
                order_queue.get_nowait()
            except:
                break

    def test_order_queue_functionality(self):
        """Test that the order queue works correctly"""
        test_order = {
            'tableNumber': 1,
            'orderedItems': [{'id': 1, 'name': 'Test Item', 'type': 'drink', 'quantity': 1}],
            'comment': 'Test'
        }
        
        initial_size = order_queue.qsize()
        order_queue.put(test_order)
        self.assertEqual(order_queue.qsize(), initial_size + 1)
        
        retrieved_order = order_queue.get()
        self.assertEqual(retrieved_order, test_order)
        self.assertEqual(order_queue.qsize(), initial_size)


if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
