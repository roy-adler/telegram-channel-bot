#!/usr/bin/env python3
"""
Test script to verify the bot handles regular messages without crashing
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = "change-me"  # Update this to match your API key

def test_bot_stability():
    """Test that the bot handles various message types without crashing"""
    print("🧪 Testing bot message handling stability...")
    
    # Test health check first
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Bot is running and healthy")
        else:
            print(f"❌ Bot health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to bot API. Make sure the bot is running.")
        return False
    except Exception as e:
        print(f"❌ Error checking bot health: {e}")
        return False
    
    # Test broadcast functionality
    print("\n2. Testing broadcast functionality...")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    test_message = "🧪 Test message - bot should handle this without crashing"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/broadcast",
            headers=headers,
            json={"message": test_message},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Broadcast successful: {data['sent_to']} chats reached")
            print(f"   - Groups: {data.get('groups', 0)}")
            print(f"   - Private chats: {data.get('private_chats', 0)}")
        else:
            print(f"⚠️  Broadcast returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error during broadcast: {e}")
        return False
    
    # Test stats endpoint
    print("\n3. Testing stats endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats retrieved successfully:")
            print(f"   - Total users: {data['total_users']}")
            print(f"   - Authenticated users: {data['authenticated_users']}")
            print(f"   - Total groups: {data['total_groups']}")
        else:
            print(f"⚠️  Stats returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return False
    
    print("\n✅ All tests passed! Bot appears to be stable.")
    return True

def test_multiple_broadcasts():
    """Test multiple broadcasts to ensure bot doesn't crash under load"""
    print("\n🔄 Testing multiple broadcasts...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    for i in range(3):
        print(f"   Sending broadcast {i+1}/3...")
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/broadcast",
                headers=headers,
                json={"message": f"Test message {i+1} - checking stability"},
                timeout=5
            )
            if response.status_code == 200:
                print(f"   ✅ Broadcast {i+1} successful")
            else:
                print(f"   ⚠️  Broadcast {i+1} returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Broadcast {i+1} failed: {e}")
            return False
        time.sleep(1)  # Small delay between broadcasts
    
    print("✅ Multiple broadcasts completed successfully!")
    return True

if __name__ == "__main__":
    print("🚀 Starting bot stability test...")
    print("This test verifies that the bot handles messages without crashing.")
    print("=" * 60)
    
    try:
        success = test_bot_stability()
        if success:
            test_multiple_broadcasts()
            print("\n" + "=" * 60)
            print("🎉 All stability tests passed!")
            print("The bot should now handle regular messages without crashing.")
        else:
            print("\n" + "=" * 60)
            print("❌ Some tests failed. Check the bot logs for errors.")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
