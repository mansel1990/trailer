#!/usr/bin/env python3
"""
Simple test script for the modular Movie API
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("Testing Modular Movie API...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
    
    # Test 2: Get movies
    print("\n2. Testing movies endpoint")
    try:
        response = requests.get(f"{base_url}/movies")
        print(f"✓ Get movies: {response.status_code}")
        if response.status_code == 200:
            movies = response.json()
            print(f"  Found {len(movies)} movies")
            if movies:
                print(f"  First movie: {movies[0]['title']}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Get movies failed: {e}")
    
    # Test 3: Get recommendations
    print("\n3. Testing recommendations endpoint")
    try:
        response = requests.get(f"{base_url}/recommendations/1?limit=3")
        print(f"✓ Get recommendations: {response.status_code}")
        if response.status_code == 200:
            recommendations = response.json()
            print(f"  Found {len(recommendations)} recommendations")
            if recommendations:
                print(f"  First recommendation: {recommendations[0]['title']}")
                print(f"  Final score: {recommendations[0]['final_score']}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Get recommendations failed: {e}")
    
    # Test 4: Get user ratings
    print("\n4. Testing user ratings endpoint")
    try:
        response = requests.get(f"{base_url}/ratings/2")
        print(f"✓ Get user ratings: {response.status_code}")
        if response.status_code == 200:
            ratings = response.json()
            print(f"  Found {len(ratings)} ratings")
            if ratings:
                print(f"  First rating: {ratings[0]['movie_title']} - {ratings[0]['rating']}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Get user ratings failed: {e}")

if __name__ == "__main__":
    test_api() 