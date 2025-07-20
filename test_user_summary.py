#!/usr/bin/env python3
"""
Test script for the user_summary endpoint
"""

import requests
import json

def test_user_summary():
    base_url = "http://localhost:8000"
    
    print("Testing User Summary API...")
    
    # Test 1: Get user summary for a valid user
    print("\n1. Testing user summary endpoint")
    try:
        response = requests.get(f"{base_url}/user_summary/1")
        print(f"✓ User summary: {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            print(f"  User ID: {summary['user_id']}")
            print(f"  Summary: {summary['summary'][:100]}...")
        elif response.status_code == 404:
            print("  User summary not found (expected for test user)")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User summary failed: {e}")
    
    # Test 2: Test with different user ID
    print("\n2. Testing with different user ID")
    try:
        response = requests.get(f"{base_url}/user_summary/2")
        print(f"✓ User summary (user 2): {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            print(f"  User ID: {summary['user_id']}")
            print(f"  Summary: {summary['summary'][:100]}...")
        elif response.status_code == 404:
            print("  User summary not found (expected for test user)")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ User summary failed: {e}")

if __name__ == "__main__":
    test_user_summary() 