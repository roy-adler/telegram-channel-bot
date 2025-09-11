#!/usr/bin/env python3
"""
Test script to verify the group broadcast functionality
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = "change-me"  # Update this to match your API key

def test_broadcast():
    """Test the broadcast functionality"""
    print("Testing broadcast functionality...")
    
    # Test data
    test_message = "🧪 Test message from group broadcast system!"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Test general broadcast
    print("\n1. Testing general broadcast...")
    response = requests.post(
        f"{API_BASE_URL}/api/broadcast",
        headers=headers,
        json={"message": test_message}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Sent to {data['sent_to']} chats")
        print(f"   - Groups: {data['groups']}")
        print(f"   - Private chats: {data['private_chats']}")
        if 'failed_chats' in data and data['failed_chats']:
            print(f"   - Failed: {len(data['failed_chats'])}")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test channel-specific broadcast
    print("\n2. Testing channel-specific broadcast...")
    response = requests.post(
        f"{API_BASE_URL}/api/broadcast-to-channel",
        headers=headers,
        json={
            "message": f"{test_message} (Channel-specific)",
            "channel": "general"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Sent to {data['sent_to']} chats in channel '{data['channel']}'")
        print(f"   - Groups: {data['groups']}")
        print(f"   - Private chats: {data['private_chats']}")
        if 'failed_chats' in data and data['failed_chats']:
            print(f"   - Failed: {len(data['failed_chats'])}")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test health check
    print("\n3. Testing health check...")
    response = requests.get(f"{API_BASE_URL}/api/health")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Bot is healthy! Authenticated users: {data['authenticated_users']}")
    else:
        print(f"❌ Error: {response.text}")

def test_stats():
    """Test the stats endpoint"""
    print("\n4. Testing stats...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    response = requests.get(f"{API_BASE_URL}/api/stats", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Stats retrieved:")
        print(f"   - Total users: {data['total_users']}")
        print(f"   - Authenticated users: {data['authenticated_users']}")
        print(f"   - Total groups: {data['total_groups']}")
        print(f"   - Total channels: {data['total_channels']}")
    else:
        print(f"❌ Error: {response.text}")

def test_debug_info():
    """Test getting debug information about groups and users"""
    print("\n5. Testing debug info...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    # Test getting all users
    response = requests.get(f"{API_BASE_URL}/api/users", headers=headers)
    print(f"Users endpoint - Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} authenticated users")
        for user in data['users'][:3]:  # Show first 3 users
            print(f"   - {user['first_name']} (@{user['username'] or 'N/A'})")
    
    # Test getting all channels
    response = requests.get(f"{API_BASE_URL}/api/channels", headers=headers)
    print(f"Channels endpoint - Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} channels")
        for channel in data['channels']:
            print(f"   - {channel['channel_name']} ({channel['user_count']} users)")

if __name__ == "__main__":
    print("🚀 Starting group broadcast test...")
    print("Make sure the bot is running and you have some authenticated users!")
    print("=" * 60)
    
    try:
        test_broadcast()
        test_stats()
        test_debug_info()
        print("\n" + "=" * 60)
        print("✅ Test completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the bot is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
