#!/usr/bin/env python3
"""
Test script to debug user preferences table structure
"""

import requests
import json

def test_debug_preferences():
    base_url = "http://localhost:8000"
    
    print("Testing Debug User Preferences Table...")
    
    try:
        response = requests.get(f"{base_url}/debug/user-preferences-table")
        print(f"✓ Debug user preferences: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Table exists: {data.get('table_exists', False)}")
            print(f"  Total records: {data.get('total_records', 0)}")
            
            print("\n  Table structure:")
            for column in data.get('structure', []):
                print(f"    - {column.get('Field', 'Unknown')}: {column.get('Type', 'Unknown')}")
            
            print("\n  Sample data:")
            for row in data.get('sample_data', [])[:3]:
                print(f"    {row}")
        else:
            print(f"  Response: {response.json()}")
            
    except Exception as e:
        print(f"✗ Debug user preferences failed: {e}")

if __name__ == "__main__":
    test_debug_preferences() 