#!/usr/bin/env python3
"""
Test script for the final user preferences movies endpoint with watched status
"""

import requests
import json

def test_user_preferences_final():
    base_url = "http://localhost:8000"
    
    print("Testing Final User Preferences Movies API...")
    
    # Test 1: Get movies based on user preferences (all movies)
    print("\n1. Testing user preferences movies (all)")
    try:
        response = requests.get(f"{base_url}/user_preferences_movies/1")
        print(f"✓ User preferences movies: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"  Found {len(results)} preference categories")
            for i, result in enumerate(results):
                print(f"  Category {i+1}: {result['title']}")
                print(f"    Found {len(result['movies'])} movies")
                if result['movies']:
                    first_movie = result['movies'][0]
                    print(f"    First movie: {first_movie['title']}")
                    print(f"    Watched: {first_movie.get('watched', 'N/A')}")
                    print(f"    Popularity: {first_movie['popularity']}")
                    print(f"    Vote Average: {first_movie['vote_average']}")
                    print(f"    Score: {first_movie['popularity'] * first_movie['vote_average']:.2f}")
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
            results = response.json()
            print(f"  Found {len(results)} preference categories")
            for i, result in enumerate(results):
                print(f"  Category {i+1}: {result['title']}")
                print(f"    Found {len(result['movies'])} watched movies")
                if result['movies']:
                    first_movie = result['movies'][0]
                    print(f"    First movie: {first_movie['title']}")
                    print(f"    Watched: {first_movie.get('watched', 'N/A')}")
                    print(f"    Score: {first_movie['popularity'] * first_movie['vote_average']:.2f}")
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
            results = response.json()
            print(f"  Found {len(results)} preference categories")
            for i, result in enumerate(results):
                print(f"  Category {i+1}: {result['title']}")
                print(f"    Found {len(result['movies'])} unwatched movies")
                if result['movies']:
                    first_movie = result['movies'][0]
                    print(f"    First movie: {first_movie['title']}")
                    print(f"    Watched: {first_movie.get('watched', 'N/A')}")
                    print(f"    Score: {first_movie['popularity'] * first_movie['vote_average']:.2f}")
        elif response.status_code == 404:
            print("  No user preferences found")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User preferences movies (unwatched) failed: {e}")

if __name__ == "__main__":
    test_user_preferences_final() 