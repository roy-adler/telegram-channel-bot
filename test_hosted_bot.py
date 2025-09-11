#!/usr/bin/env python3
"""
Test script for hosted Telegram bot API
"""

import requests
import json
import time
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://telegram-bot-api.royadler.de"
API_KEY = "asdfghjkl"  # Update this to match your actual API key

def test_connectivity():
    """Test basic connectivity to the hosted API"""
    print("🌐 Testing connectivity to hosted bot...")
    print(f"   URL: {BASE_URL}")
    
    # Test different possible endpoints
    endpoints_to_test = [
        "/api/health",
        "/health", 
        "/",
        "/api/",
        "/api"
    ]
    
    for endpoint in endpoints_to_test:
        url = urljoin(BASE_URL, endpoint)
        print(f"\n   Testing: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   📊 JSON Data: {data}")
                except:
                    print(f"   📄 Text Response: {response.text}")
                return url  # Return the working endpoint
                
        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL Error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection Error: {e}")
        except requests.exceptions.Timeout as e:
            print(f"   ❌ Timeout Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

def test_health_endpoint(working_url):
    """Test the health endpoint specifically"""
    print(f"\n🏥 Testing health endpoint...")
    
    try:
        response = requests.get(working_url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check successful!")
            print(f"   📊 Data: {data}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_api_endpoints():
    """Test various API endpoints"""
    print(f"\n🔌 Testing API endpoints...")
    
    headers = {"X-API-Key": API_KEY}
    endpoints = [
        "/api/users",
        "/api/channels", 
        "/api/stats"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints:
        url = urljoin(BASE_URL, endpoint)
        print(f"\n   Testing: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                print(f"   📊 Response: {json.dumps(data, indent=2)[:300]}...")
                working_endpoints.append(endpoint)
            elif response.status_code == 401:
                print(f"   🔐 Unauthorized - API key might be wrong")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return working_endpoints

def test_broadcast():
    """Test the broadcast functionality"""
    print(f"\n📡 Testing broadcast functionality...")
    
    url = urljoin(BASE_URL, "/api/broadcast")
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    test_message = "🧪 Test message from hosted bot API"
    body = {"message": test_message}
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Broadcast successful!")
            print(f"   📊 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"   ❌ Broadcast failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Broadcast error: {e}")
        return False

def test_ssl_and_certificates():
    """Test SSL and certificate issues"""
    print(f"\n🔒 Testing SSL and certificates...")
    
    try:
        # Test with SSL verification
        response = requests.get(f"{BASE_URL}/api/health", timeout=10, verify=True)
        print(f"   ✅ SSL verification successful")
        return True
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        print(f"   💡 Try with verify=False for testing")
        
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10, verify=False)
            print(f"   ⚠️  Works with SSL verification disabled")
            return "no_ssl"
        except Exception as e2:
            print(f"   ❌ Still fails: {e2}")
            return False
    except Exception as e:
        print(f"   ❌ Other error: {e}")
        return False

def main():
    print("🚀 Testing hosted Telegram bot API")
    print("=" * 60)
    print(f"🌐 Target: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY}")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    working_url = test_connectivity()
    if not working_url:
        print("\n❌ Cannot reach the hosted API at any endpoint")
        print("💡 Check if:")
        print("   - The URL is correct")
        print("   - The server is running")
        print("   - The domain is accessible")
        return
    
    print(f"\n✅ Found working endpoint: {working_url}")
    
    # Test 2: SSL/Certificates
    ssl_status = test_ssl_and_certificates()
    
    # Test 3: Health endpoint
    if test_health_endpoint(working_url):
        print("\n✅ Health check passed!")
    else:
        print("\n❌ Health check failed")
        return
    
    # Test 4: API endpoints
    working_endpoints = test_api_endpoints()
    if working_endpoints:
        print(f"\n✅ Found {len(working_endpoints)} working API endpoints")
    else:
        print("\n❌ No API endpoints are working")
        print("💡 Check if the API key is correct")
        return
    
    # Test 5: Broadcast functionality
    if test_broadcast():
        print("\n🎉 Broadcast test successful!")
        print("✅ Your hosted bot API is working correctly!")
    else:
        print("\n❌ Broadcast test failed")
        print("💡 Check if there are authenticated users in the bot")
    
    print("\n" + "=" * 60)
    print("🏁 Testing completed!")

if __name__ == "__main__":
    main()
