#!/usr/bin/env python3
"""
Simple test for recommendations endpoint
"""

import requests

def test_simple_recommendations():
    base_url = "http://localhost:8000"
    
    print("Simple Recommendations Test")
    print("=" * 30)
    
    # Test with user 1 - no filter
    print("\n1. Testing user 1 without filter:")
    try:
        response = requests.get(f"{base_url}/recommendations/1")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} recommendations")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test with user 1 - watched=false
    print("\n2. Testing user 1 with watched=false:")
    try:
        response = requests.get(f"{base_url}/recommendations/1?watched=false")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} recommendations")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_simple_recommendations() 