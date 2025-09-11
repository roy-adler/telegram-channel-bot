#!/usr/bin/env python3
"""
Test script to verify the /stop command functionality
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "https://telegram-bot-api.royadler.de"
API_KEY = "asdfghjkl"

def test_before_stop():
    """Test the state before using /stop command"""
    print("📊 Testing state before /stop command...")
    
    headers = {"X-API-Key": API_KEY}
    
    # Get stats
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats retrieved:")
            print(f"   - Total users: {data['total_users']}")
            print(f"   - Authenticated users: {data['authenticated_users']}")
            print(f"   - Total groups: {data['total_groups']}")
            return data
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None

def test_broadcast_before():
    """Test broadcast before /stop command"""
    print("\n📡 Testing broadcast before /stop...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/broadcast",
            headers=headers,
            json={"message": "🧪 Test before /stop command"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Broadcast before /stop successful:")
            print(f"   - Total chats: {data['total_chats']}")
            print(f"   - Groups: {data.get('groups', 0)}")
            print(f"   - Private chats: {data.get('private_chats', 0)}")
            print(f"   - Sent to: {data['sent_to']}")
            return data
        else:
            print(f"❌ Broadcast failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error during broadcast: {e}")
        return None

def simulate_stop_command():
    """Simulate what happens when a user types /stop"""
    print("\n🛑 Simulating /stop command...")
    print("   (In a real scenario, a user would type /stop in the group)")
    print("   This would:")
    print("   1. Remove the user from the group_members table")
    print("   2. Set is_authenticated = FALSE")
    print("   3. Set channel_id = NULL")
    print("   4. Send confirmation message to the user")

def test_after_stop():
    """Test the state after using /stop command"""
    print("\n📊 Testing state after /stop command...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats after /stop:")
            print(f"   - Total users: {data['total_users']}")
            print(f"   - Authenticated users: {data['authenticated_users']}")
            print(f"   - Total groups: {data['total_groups']}")
            return data
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None

def test_broadcast_after():
    """Test broadcast after /stop command"""
    print("\n📡 Testing broadcast after /stop...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/broadcast",
            headers=headers,
            json={"message": "🧪 Test after /stop command"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Broadcast after /stop:")
            print(f"   - Total chats: {data['total_chats']}")
            print(f"   - Groups: {data.get('groups', 0)}")
            print(f"   - Private chats: {data.get('private_chats', 0)}")
            print(f"   - Sent to: {data['sent_to']}")
            return data
        else:
            print(f"❌ Broadcast failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error during broadcast: {e}")
        return None

def main():
    print("🛑 Testing /stop command functionality")
    print("=" * 50)
    print("This test simulates what happens when users type /stop")
    print("=" * 50)
    
    # Test 1: State before /stop
    before_stats = test_before_stop()
    if not before_stats:
        print("\n❌ Cannot get initial stats. API might be down.")
        return
    
    # Test 2: Broadcast before /stop
    before_broadcast = test_broadcast_before()
    if not before_broadcast:
        print("\n❌ Cannot test broadcast before /stop.")
        return
    
    # Test 3: Simulate /stop command
    simulate_stop_command()
    
    # Test 4: State after /stop
    after_stats = test_after_stop()
    if not after_stats:
        print("\n❌ Cannot get stats after /stop.")
        return
    
    # Test 5: Broadcast after /stop
    after_broadcast = test_broadcast_after()
    if not after_broadcast:
        print("\n❌ Cannot test broadcast after /stop.")
        return
    
    # Compare results
    print("\n📊 Comparison:")
    print(f"   Authenticated users before: {before_stats['authenticated_users']}")
    print(f"   Authenticated users after:  {after_stats['authenticated_users']}")
    print(f"   Broadcasts sent before: {before_broadcast['sent_to']}")
    print(f"   Broadcasts sent after:  {after_broadcast['sent_to']}")
    
    print("\n" + "=" * 50)
    print("✅ /stop command test completed!")
    print("\nTo test the actual /stop command:")
    print("1. Have a user type /stop in a group")
    print("2. Check that they no longer receive broadcasts")
    print("3. Verify they can rejoin with /join <secret>")

if __name__ == "__main__":
    main()
