#!/usr/bin/env python3
"""
Simple test script to verify the authentication system is working
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_auth_endpoints():
    session = requests.Session()
    
    print("Testing Authentication System")
    print("=" * 40)
    
    # Test 1: Check initial auth status
    print("1. Checking initial auth status...")
    try:
        response = session.get(f"{BASE_URL}/auth/check")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Try login with admin credentials
    print("\n2. Testing login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Check auth status after login
    print("\n3. Checking auth status after login...")
    try:
        response = session.get(f"{BASE_URL}/auth/check")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Try to access a protected endpoint (place order)
    print("\n4. Testing protected endpoint (orders)...")
    try:
        response = session.get(f"{BASE_URL}/orders")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\nTesting complete!")

if __name__ == "__main__":
    test_auth_endpoints()
