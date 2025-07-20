#!/usr/bin/env python3
"""
Test script to check table structures
"""

import requests
import json

def test_table_structure():
    base_url = "http://localhost:8000"
    
    print("Testing Table Structure Debug...")
    
    # Test movie_cast table
    print("\n1. Testing movie_cast table structure")
    try:
        response = requests.get(f"{base_url}/debug/table-structure/movie_cast")
        print(f"✓ movie_cast structure: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Table: {data.get('table_name')}")
            print("  Structure:")
            for column in data.get('structure', []):
                print(f"    - {column.get('Field', 'Unknown')}: {column.get('Type', 'Unknown')}")
            print("  Sample data:")
            for row in data.get('sample_data', [])[:2]:
                print(f"    {row}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ movie_cast structure failed: {e}")
    
    # Test movie_crew table
    print("\n2. Testing movie_crew table structure")
    try:
        response = requests.get(f"{base_url}/debug/table-structure/movie_crew")
        print(f"✓ movie_crew structure: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Table: {data.get('table_name')}")
            print("  Structure:")
            for column in data.get('structure', []):
                print(f"    - {column.get('Field', 'Unknown')}: {column.get('Type', 'Unknown')}")
            print("  Sample data:")
            for row in data.get('sample_data', [])[:2]:
                print(f"    {row}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ movie_crew structure failed: {e}")
    
    # Test tmdb_movie_genres table
    print("\n3. Testing tmdb_movie_genres table structure")
    try:
        response = requests.get(f"{base_url}/debug/table-structure/tmdb_movie_genres")
        print(f"✓ tmdb_movie_genres structure: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Table: {data.get('table_name')}")
            print("  Structure:")
            for column in data.get('structure', []):
                print(f"    - {column.get('Field', 'Unknown')}: {column.get('Type', 'Unknown')}")
            print("  Sample data:")
            for row in data.get('sample_data', [])[:2]:
                print(f"    {row}")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ tmdb_movie_genres structure failed: {e}")

if __name__ == "__main__":
    test_table_structure() 