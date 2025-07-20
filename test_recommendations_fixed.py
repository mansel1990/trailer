#!/usr/bin/env python3
"""
Test script for the fixed recommendations endpoint
"""

import requests
import json

def test_recommendations_fixed():
    base_url = "http://localhost:8000"
    
    print("Testing Fixed Recommendations Endpoint")
    print("=" * 40)
    
    # Test 1: Check recommendations for user 1 (has data)
    print("\n1. Testing recommendations for user 1 (has data):")
    try:
        response = requests.get(f"{base_url}/recommendations/1")
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"  Found {len(results)} recommendations")
            if results:
                print(f"  First recommendation: {results[0]}")
                print(f"  - Title: {results[0].get('title')}")
                print(f"  - Predicted Star Rating: {results[0].get('predicted_star_rating')}")
                print(f"  - User Rating: {results[0].get('user_rating')}")
                print(f"  - Watched: {results[0].get('watched')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Check recommendations with watched=false for user 1
    print("\n2. Testing recommendations with watched=false for user 1:")
    try:
        response = requests.get(f"{base_url}/recommendations/1?watched=false")
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"  Found {len(results)} unwatched recommendations")
            if results:
                print(f"  First unwatched recommendation: {results[0]}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Check recommendations with watched=true for user 1
    print("\n3. Testing recommendations with watched=true for user 1:")
    try:
        response = requests.get(f"{base_url}/recommendations/1?watched=true")
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"  Found {len(results)} watched recommendations")
            if results:
                print(f"  First watched recommendation: {results[0]}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Check recommendations for user 2 (no data)
    print("\n4. Testing recommendations for user 2 (no data):")
    try:
        response = requests.get(f"{base_url}/recommendations/2")
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"  Found {len(results)} recommendations")
            if not results:
                print("  ✅ Correctly returned empty list for user with no data")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_recommendations_fixed() 