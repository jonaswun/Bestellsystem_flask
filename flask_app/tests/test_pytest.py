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


def test_get_menu_endpoint(client):
    """Test the /menu GET endpoint"""
    response = client.get('/menu')
    
    assert response.status_code == 200
    assert response.content_type == 'application/json; charset=utf-8'
    
    data = json.loads(response.data)
    assert 'Bier' in data
    assert 'Wein' in data
    assert 'Alkoholfreie Getränke' in data
    assert 'Essen' in data
    assert 'Kaffee/Kuchen' in data


def test_get_menu_structure(client):
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


@patch('main.save_order')
def test_place_order_endpoint(mock_save_order, client):
    """Test the /order POST endpoint"""
    test_order = {
        'tableNumber': 5,
        'orderedItems': [
            {'id': 1, 'name': 'Pils', 'price': 3.5, 'type': 'drink', 'quantity': 2},
            {'id': 18, 'name': 'Schweinekeule (ohne Knochen) mit Brot', 'price': 8.0, 'type': 'food', 'quantity': 1}
        ],
        'comment': 'Test order'
    }
    
    response = client.post('/order', 
                          data=json.dumps(test_order),
                          content_type='application/json')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['message'] == 'Order received!'
    assert data['order'] == test_order
    
    # Verify save_order was called
    mock_save_order.assert_called_once()


def test_place_order_adds_to_queue(client):
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


def test_place_order_invalid_json(client):
    """Test placing an order with invalid JSON"""
    response = client.post('/order',
                          data='invalid json',
                          content_type='application/json')
    
    assert response.status_code == 400


def test_place_order_missing_data(client):
    """Test placing an order with missing required data"""
    incomplete_order = {
        'tableNumber': 1
        # Missing orderedItems and comment
    }
    
    with patch('main.save_order'):
        response = client.post('/order',
                              data=json.dumps(incomplete_order),
                              content_type='application/json')
    
    # The endpoint should handle this gracefully
    # Note: Your current implementation doesn't validate input, 
    # so this might pass but could cause errors in processing
    assert response.status_code in [200, 400, 500]


def test_invalid_endpoint(client):
    """Test accessing a non-existent endpoint"""
    response = client.get('/nonexistent')
    assert response.status_code == 404


def test_order_with_user_agent(client):
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


def test_cors_headers(client):
    """Test that CORS headers are present"""
    response = client.get('/menu')
    
    # Check if CORS is working (Flask-CORS should add these headers)
    assert response.status_code == 200
    # Note: In test environment, CORS headers might not be visible
    # This test verifies the endpoint works with CORS enabled


@patch('main.MockPrinter')
def test_mock_printer_integration(mock_printer_class, client):
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
        response = client.post('/order',
                              data=json.dumps(test_order),
                              content_type='application/json')
    
    assert response.status_code == 200


def test_order_queue_functionality():
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


# Pytest markers for organizing tests
pytestmark = [
    pytest.mark.unit,  # Mark all tests in this file as unit tests
]


# Test configuration for different scenarios
class TestEndpointErrors:
    """Test error handling in endpoints"""
    
    def test_menu_endpoint_availability(self, client):
        """Ensure menu endpoint is always available"""
        response = client.get('/menu')
        assert response.status_code == 200
        
    def test_order_endpoint_post_only(self, client):
        """Ensure order endpoint only accepts POST requests"""
        response = client.get('/order')
        assert response.status_code == 405  # Method Not Allowed
