import requests
import json

# Test data
test_order = {
    "tableNumber": 5,
    "orderedItems": [
        {
            "id": 1,
            "name": "Pils",
            "price": 3.5,
            "type": "drink",
            "quantity": 2
        },
        {
            "id": 18,
            "name": "Schweinekeule (ohne Knochen) mit Brot",
            "price": 8.0,
            "type": "food",
            "quantity": 1
        }
    ],
    "comment": "Test order from Python script"
}

def test_order_endpoint():
    """Test the /order endpoint"""
    try:
        # Test POST /order
        print("Testing POST /order...")
        response = requests.post(
            'http://localhost:5000/order',
            json=test_order,
            headers={'User-Agent': 'TestClient/1.0'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Order endpoint is working!")
            return True
        else:
            print("❌ Order endpoint failed!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_menu_endpoint():
    """Test the /menu endpoint"""
    try:
        print("\nTesting GET /menu...")
        response = requests.get('http://localhost:5000/menu')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Menu categories: {list(data.keys())}")
            print("✅ Menu endpoint is working!")
            return True
        else:
            print("❌ Menu endpoint failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing menu endpoint: {e}")
        return False

def test_new_endpoints():
    """Test the new SQLite endpoints"""
    try:
        print("\nTesting new SQLite endpoints...")
        
        # Test GET /orders
        print("Testing GET /orders...")
        response = requests.get('http://localhost:5000/orders?limit=5')
        print(f"Orders Status Code: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            print(f"Retrieved {len(orders.get('orders', []))} orders")
            print("✅ Orders endpoint is working!")
        
        # Test GET /analytics/sales
        print("\nTesting GET /analytics/sales...")
        response = requests.get('http://localhost:5000/analytics/sales')
        print(f"Sales Status Code: {response.status_code}")
        
        if response.status_code == 200:
            sales = response.json()
            print(f"Sales data: {sales}")
            print("✅ Sales analytics endpoint is working!")
        
        # Test GET /analytics/popular-items
        print("\nTesting GET /analytics/popular-items...")
        response = requests.get('http://localhost:5000/analytics/popular-items')
        print(f"Popular Items Status Code: {response.status_code}")
        
        if response.status_code == 200:
            items = response.json()
            print(f"Popular items: {items}")
            print("✅ Popular items endpoint is working!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing new endpoints: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Flask Ordering System Endpoints")
    print("=" * 50)
    
    # Test basic endpoints
    menu_ok = test_menu_endpoint()
    order_ok = test_order_endpoint()
    
    # Test new SQLite endpoints
    new_endpoints_ok = test_new_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Menu endpoint: {'✅ PASS' if menu_ok else '❌ FAIL'}")
    print(f"Order endpoint: {'✅ PASS' if order_ok else '❌ FAIL'}")
    print(f"New SQLite endpoints: {'✅ PASS' if new_endpoints_ok else '❌ FAIL'}")
    
    if all([menu_ok, order_ok, new_endpoints_ok]):
        print("\n🎉 All endpoints are working correctly!")
    else:
        print("\n⚠️ Some endpoints have issues!")
