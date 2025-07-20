#!/usr/bin/env python3
"""
Test script to debug available tables
"""

import requests
import json

def test_debug_tables():
    base_url = "http://localhost:8000"
    
    print("Testing Debug Available Tables...")
    
    try:
        response = requests.get(f"{base_url}/debug/available-tables")
        print(f"✓ Debug available tables: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  All tables: {len(data.get('all_tables', []))}")
            print(f"  Cast-related tables: {data.get('cast_related', [])}")
            print(f"  Crew-related tables: {data.get('crew_related', [])}")
            print(f"  Genre-related tables: {data.get('genre_related', [])}")
            
            print("\n  All tables:")
            for table in data.get('all_tables', [])[:10]:  # Show first 10
                print(f"    - {table}")
        else:
            print(f"  Response: {response.json()}")
            
    except Exception as e:
        print(f"✗ Debug available tables failed: {e}")

if __name__ == "__main__":
    test_debug_tables() 