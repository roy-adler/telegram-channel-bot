#!/usr/bin/env python3
"""
Test script to verify the bot handles messages without crashing
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = "change-me"  # Update this to match your API key

def test_bot_health():
    """Test that the bot is running and healthy"""
    print("🏥 Testing bot health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Bot is healthy!")
            print(f"   - Status: {data['status']}")
            print(f"   - Authenticated users: {data['authenticated_users']}")
            return True
        else:
            print(f"❌ Bot health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to bot API. Make sure the bot is running.")
        return False
    except Exception as e:
        print(f"❌ Error checking bot health: {e}")
        return False

def test_broadcast_stability():
    """Test multiple broadcasts to ensure bot doesn't crash"""
    print("\n📡 Testing broadcast stability...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    test_messages = [
        "🧪 Test message 1 - checking stability",
        "🧪 Test message 2 - bot should handle this",
        "🧪 Test message 3 - no crashes please",
        "🧪 Test message 4 - final stability check"
    ]
    
    success_count = 0
    
    for i, message in enumerate(test_messages, 1):
        print(f"   Sending test message {i}/{len(test_messages)}...")
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/broadcast",
                headers=headers,
                json={"message": message},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Message {i} sent successfully to {data['sent_to']} chats")
                success_count += 1
            else:
                print(f"   ⚠️  Message {i} returned status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Message {i} failed: {e}")
        
        # Small delay between messages
        time.sleep(2)
    
    print(f"\n📊 Results: {success_count}/{len(test_messages)} messages sent successfully")
    return success_count == len(test_messages)

def test_api_endpoints():
    """Test various API endpoints to ensure they work"""
    print("\n🔌 Testing API endpoints...")
    
    headers = {"X-API-Key": API_KEY}
    endpoints = [
        ("/api/users", "GET"),
        ("/api/channels", "GET"),
        ("/api/stats", "GET")
    ]
    
    success_count = 0
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=5)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - OK")
                success_count += 1
            else:
                print(f"   ⚠️  {endpoint} - Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
    
    print(f"\n📊 API Results: {success_count}/{len(endpoints)} endpoints working")
    return success_count == len(endpoints)

def main():
    print("🚀 Starting bot stability test...")
    print("This test verifies that the bot handles messages without crashing.")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_bot_health():
        print("\n❌ Bot is not healthy. Please check the logs and restart.")
        return
    
    # Test 2: API endpoints
    if not test_api_endpoints():
        print("\n⚠️  Some API endpoints are not working properly.")
    
    # Test 3: Broadcast stability
    if test_broadcast_stability():
        print("\n🎉 All stability tests passed!")
        print("The bot should now handle regular messages without crashing.")
    else:
        print("\n⚠️  Some broadcast tests failed, but bot is still running.")
    
    print("\n" + "=" * 60)
    print("✅ Stability test completed!")
    print("\nBot Commands for Users:")
    print("- /start - Start the bot")
    print("- /join <secret> - Join a channel")
    print("- /register - Register in current group")
    print("- /status - Check authentication status")
    print("- /leave - Leave current channel")

if __name__ == "__main__":
    main()
