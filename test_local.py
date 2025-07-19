#!/usr/bin/env python3
"""
Simple test script to verify the API works locally
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("Testing Movie Trailer API...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Root endpoint: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✓ Health endpoint: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
    
    # Test movies endpoint
    try:
        response = requests.get(f"{base_url}/movies")
        print(f"✓ Movies endpoint: {response.status_code}")
        if response.status_code == 200:
            movies = response.json()
            print(f"  Found {len(movies)} movies")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Movies endpoint failed: {e}")

if __name__ == "__main__":
    test_api() 