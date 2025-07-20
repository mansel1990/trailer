#!/usr/bin/env python3
"""
Test script for movie recommendations endpoint
"""

import requests
import json

def test_recommendations():
    base_url = "http://localhost:8000"
    
    print("Testing Movie Recommendations API...")
    
    # Test data
    test_user_id = "1"  # User with recommendations
    
    # Test 1: Get all recommendations
    print("\n1. Testing GET /recommendations/{clerk_user_id} (all)")
    try:
        response = requests.get(f"{base_url}/recommendations/{test_user_id}?limit=5")
        print(f"✓ Get recommendations: {response.status_code}")
        if response.status_code == 200:
            recommendations = response.json()
            print(f"  Found {len(recommendations)} recommendations")
            if recommendations:
                print(f"  First recommendation: {recommendations[0]['title']}")
                print(f"  Predicted score: {recommendations[0]['predicted_score']}")
                print(f"  Final score: {recommendations[0]['final_score']}")
                print(f"  Watched: {recommendations[0]['watched']}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Get recommendations failed: {e}")
    
    # Test 2: Get unwatched recommendations only
    print("\n2. Testing GET /recommendations/{clerk_user_id} (unwatched only)")
    try:
        response = requests.get(f"{base_url}/recommendations/{test_user_id}?watched=false&limit=5")
        print(f"✓ Get unwatched recommendations: {response.status_code}")
        if response.status_code == 200:
            recommendations = response.json()
            print(f"  Found {len(recommendations)} unwatched recommendations")
            if recommendations:
                print(f"  First recommendation: {recommendations[0]['title']}")
                print(f"  Watched: {recommendations[0]['watched']}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Get unwatched recommendations failed: {e}")
    
    # Test 3: Get watched recommendations only
    print("\n3. Testing GET /recommendations/{clerk_user_id} (watched only)")
    try:
        response = requests.get(f"{base_url}/recommendations/{test_user_id}?watched=true&limit=5")
        print(f"✓ Get watched recommendations: {response.status_code}")
        if response.status_code == 200:
            recommendations = response.json()
            print(f"  Found {len(recommendations)} watched recommendations")
            if recommendations:
                print(f"  First recommendation: {recommendations[0]['title']}")
                print(f"  Watched: {recommendations[0]['watched']}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Get watched recommendations failed: {e}")

if __name__ == "__main__":
    test_recommendations() 