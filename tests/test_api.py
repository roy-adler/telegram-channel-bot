#!/usr/bin/env python3
"""
Simple test script to verify the API functionality
"""
import requests
import json

def test_api():
    base_url = "http://localhost:5000/api"
    
    print("Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test users endpoint (should fail without API key)
    try:
        response = requests.get(f"{base_url}/users")
        print(f"Users (no auth): {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication working correctly")
        else:
            print(f"Unexpected response: {response.text}")
    except Exception as e:
        print(f"Users test failed: {e}")
    
    # Test users endpoint with API key
    try:
        headers = {"X-API-Key": "change-me"}
        response = requests.get(f"{base_url}/users", headers=headers)
        print(f"Users (with auth): {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Users with auth test failed: {e}")
    
    # Test stats endpoint
    try:
        headers = {"X-API-Key": "change-me"}
        response = requests.get(f"{base_url}/stats", headers=headers)
        print(f"Stats: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Stats test failed: {e}")
    
    # Test broadcast endpoint
    try:
        headers = {"X-API-Key": "change-me", "Content-Type": "application/json"}
        data = {"message": "Test broadcast message"}
        response = requests.post(f"{base_url}/broadcast", headers=headers, json=data)
        print(f"Broadcast: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Broadcast test failed: {e}")

if __name__ == "__main__":
    test_api()
