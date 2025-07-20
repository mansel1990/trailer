#!/usr/bin/env python3
"""
Test script for the login API endpoint
"""

import requests
import json

def test_login_api():
    base_url = "http://localhost:8000"
    
    print("Testing Login API")
    print("=" * 50)
    
    # Test 1: New user registration
    print("\n1. Testing new user registration")
    payload = {
        "clerkUserId": "user_test123",
        "email": "test@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "imageUrl": "https://example.com/image.jpg",
        "username": "johndoe123"
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=payload)
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Message: {result.get('message')}")
            print(f"  Status: {result.get('status')}")
            print(f"  Clerk User ID: {result.get('clerk_user_id')}")
            print(f"  Username: {result.get('username')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Duplicate username (should fail)
    print("\n2. Testing duplicate username (should fail)")
    payload2 = {
        "clerkUserId": "user_test456",
        "email": "test2@example.com",
        "firstName": "Jane",
        "lastName": "Smith",
        "imageUrl": "https://example.com/image2.jpg",
        "username": "johndoe123"  # Same username as above
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=payload2)
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            print(f"  Error: {result.get('detail')}")
            print("  ✓ Correctly rejected duplicate username")
        else:
            print(f"  Unexpected response: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Existing user (should return "updated")
    print("\n3. Testing existing user (should return 'updated')")
    payload3 = {
        "clerkUserId": "user_test123",  # Same as first test
        "email": "test@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "imageUrl": "https://example.com/image.jpg",
        "username": "johndoe123"
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=payload3)
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Message: {result.get('message')}")
            print(f"  Status: {result.get('status')}")
            print("  ✓ Correctly updated existing user")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: User without username
    print("\n4. Testing user without username")
    payload4 = {
        "clerkUserId": "user_test789",
        "email": "test3@example.com",
        "firstName": "Bob",
        "lastName": "Johnson",
        "imageUrl": "https://example.com/image3.jpg"
        # No username field
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=payload4)
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Message: {result.get('message')}")
            print(f"  Status: {result.get('status')}")
            print("  ✓ Successfully registered user without username")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_login_api() 