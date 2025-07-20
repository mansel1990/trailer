#!/usr/bin/env python3
"""
Test script for the user preferences movies endpoint
"""

import requests
import json

def test_user_preferences():
    base_url = "http://localhost:8000"
    
    print("Testing User Preferences Movies API...")
    
    # Test 1: Get movies based on user preferences (all movies)
    print("\n1. Testing user preferences movies (all)")
    try:
        response = requests.get(f"{base_url}/user_preferences_movies/1")
        print(f"✓ User preferences movies: {response.status_code}")
        if response.status_code == 200:
            movies = response.json()
            print(f"  Found {len(movies)} movies based on preferences")
            if movies:
                print(f"  First movie: {movies[0]['title']}")
                print(f"  Popularity score: {movies[0]['popularity_score']}")
        elif response.status_code == 404:
            print("  No user preferences found")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User preferences movies failed: {e}")
    
    # Test 2: Get movies based on user preferences (watched only)
    print("\n2. Testing user preferences movies (watched only)")
    try:
        response = requests.get(f"{base_url}/user_preferences_movies/1?watched=true")
        print(f"✓ User preferences movies (watched): {response.status_code}")
        if response.status_code == 200:
            movies = response.json()
            print(f"  Found {len(movies)} watched movies based on preferences")
            if movies:
                print(f"  First movie: {movies[0]['title']}")
        elif response.status_code == 404:
            print("  No user preferences found")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User preferences movies (watched) failed: {e}")
    
    # Test 3: Get movies based on user preferences (unwatched only)
    print("\n3. Testing user preferences movies (unwatched only)")
    try:
        response = requests.get(f"{base_url}/user_preferences_movies/1?watched=false")
        print(f"✓ User preferences movies (unwatched): {response.status_code}")
        if response.status_code == 200:
            movies = response.json()
            print(f"  Found {len(movies)} unwatched movies based on preferences")
            if movies:
                print(f"  First movie: {movies[0]['title']}")
        elif response.status_code == 404:
            print("  No user preferences found")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User preferences movies (unwatched) failed: {e}")
    
    # Test 4: Test with different user ID
    print("\n4. Testing with different user ID")
    try:
        response = requests.get(f"{base_url}/user_preferences_movies/2")
        print(f"✓ User preferences movies (user 2): {response.status_code}")
        if response.status_code == 200:
            movies = response.json()
            print(f"  Found {len(movies)} movies based on preferences")
            if movies:
                print(f"  First movie: {movies[0]['title']}")
        elif response.status_code == 404:
            print("  No user preferences found (expected for test user)")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User preferences movies (user 2) failed: {e}")

if __name__ == "__main__":
    test_user_preferences() 