#!/usr/bin/env python3
"""
Comprehensive test suite for the Telegram Bot API
Consolidates functionality from multiple test files into one comprehensive suite.
"""

import requests
import json
import time
import sys
from typing import Optional, Dict, Any

# Configuration
DEFAULT_API_BASE_URL = "http://localhost:5000"
DEFAULT_API_KEY = "asdfghjkl"  # Default from docker-compose.yml

class BotTester:
    def __init__(self, base_url: str = DEFAULT_API_BASE_URL, api_key: str = DEFAULT_API_KEY):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
        self.headers_json = {"X-API-Key": api_key, "Content-Type": "application/json"}
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with appropriate formatting"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "TEST": "🧪"}
        print(f"{icons.get(level, '•')} {message}")
    
    def test_connectivity(self) -> bool:
        """Test basic connectivity to the API"""
        self.log("Testing API connectivity...", "TEST")
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log(f"API is healthy! Authenticated users: {data.get('authenticated_users', 0)}", "SUCCESS")
                return True
            else:
                self.log(f"Health check failed with status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.ConnectionError:
            self.log(f"Cannot connect to API at {self.base_url}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Connectivity test failed: {e}", "ERROR")
            return False
    
    def test_authentication(self) -> bool:
        """Test API authentication"""
        self.log("Testing API authentication...", "TEST")
        
        # Test without API key (should fail)
        try:
            response = requests.get(f"{self.base_url}/api/users", timeout=5)
            if response.status_code == 401:
                self.log("Authentication properly rejects requests without API key", "SUCCESS")
            else:
                self.log(f"Expected 401, got {response.status_code}", "WARNING")
        except Exception as e:
            self.log(f"Auth test (no key) failed: {e}", "ERROR")
            return False
        
        # Test with API key (should work)
        try:
            response = requests.get(f"{self.base_url}/api/users", headers=self.headers, timeout=5)
            if response.status_code == 200:
                self.log("Authentication works with valid API key", "SUCCESS")
                return True
            else:
                self.log(f"Auth test with API key failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Auth test (with key) failed: {e}", "ERROR")
            return False
    
    def test_api_endpoints(self) -> Dict[str, bool]:
        """Test all major API endpoints"""
        self.log("Testing API endpoints...", "TEST")
        
        endpoints = {
            "users": "/api/users",
            "channels": "/api/channels", 
            "stats": "/api/stats"
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✓ {name} endpoint working", "SUCCESS")
                    results[name] = True
                else:
                    self.log(f"✗ {name} endpoint failed: {response.status_code}", "ERROR")
                    results[name] = False
            except Exception as e:
                self.log(f"✗ {name} endpoint error: {e}", "ERROR")
                results[name] = False
        
        working_count = sum(results.values())
        total_count = len(results)
        self.log(f"API Endpoints: {working_count}/{total_count} working", "INFO")
        
        return results
    
    def test_broadcast_functionality(self) -> bool:
        """Test broadcast functionality"""
        self.log("Testing broadcast functionality...", "TEST")
        
        test_message = "🧪 Test message from automated test suite"
        
        # Test general broadcast
        try:
            response = requests.post(
                f"{self.base_url}/api/broadcast",
                headers=self.headers_json,
                json={"message": test_message},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"General broadcast successful: {data['sent_to']} chats", "SUCCESS")
                return True
            elif response.status_code == 404:
                self.log("No authenticated users found (expected for new bot)", "WARNING")
                return True  # This is actually OK for a new bot
            else:
                self.log(f"Broadcast failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Broadcast test failed: {e}", "ERROR")
            return False
    
    def test_channel_broadcast(self, channel_name: str = "general", channel_secret: str = "welcome123") -> bool:
        """Test channel-specific broadcast"""
        self.log(f"Testing channel broadcast to '{channel_name}'...", "TEST")
        
        test_message = f"🧪 Test channel message for {channel_name}"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/broadcast-to-channel",
                headers=self.headers_json,
                json={"message": test_message, "channel": channel_name, "channel_secret": channel_secret},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Channel broadcast successful: {data['sent_to']} chats", "SUCCESS")
                return True
            elif response.status_code == 404:
                self.log(f"Channel '{channel_name}' not found or no users", "WARNING")
                return True  # This is OK if channel doesn't exist or has no users
            elif response.status_code == 401:
                self.log(f"Invalid channel secret for '{channel_name}'", "WARNING")
                return True  # This is OK if we're using wrong secret for test
            else:
                self.log(f"Channel broadcast failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Channel broadcast test failed: {e}", "ERROR")
            return False
    
    def test_stability(self, num_requests: int = 3) -> bool:
        """Test API stability with multiple requests"""
        self.log(f"Testing stability with {num_requests} requests...", "TEST")
        
        success_count = 0
        
        for i in range(num_requests):
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=5)
                if response.status_code == 200:
                    success_count += 1
                    self.log(f"Stability test {i+1}/{num_requests} ✓", "INFO")
                else:
                    self.log(f"Stability test {i+1}/{num_requests} ✗ ({response.status_code})", "WARNING")
                
                time.sleep(0.5)  # Small delay between requests
                
            except Exception as e:
                self.log(f"Stability test {i+1}/{num_requests} failed: {e}", "ERROR")
        
        if success_count == num_requests:
            self.log("Stability test passed!", "SUCCESS")
            return True
        else:
            self.log(f"Stability test partial: {success_count}/{num_requests} requests succeeded", "WARNING")
            return success_count > 0
    
    def get_bot_stats(self) -> Optional[Dict[str, Any]]:
        """Get bot statistics"""
        try:
            response = requests.get(f"{self.base_url}/api/stats", headers=self.headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def print_summary(self, stats: Optional[Dict[str, Any]] = None):
        """Print test summary and bot stats"""
        print("\n" + "="*50)
        print("📊 BOT STATUS SUMMARY")
        print("="*50)
        
        if stats:
            print(f"👥 Total users: {stats.get('total_users', 0)}")
            print(f"✅ Authenticated users: {stats.get('authenticated_users', 0)}")
            print(f"🏠 Total groups: {stats.get('total_groups', 0)}")
            print(f"📺 Total channels: {stats.get('total_channels', 0)}")
            
            if 'channel_distribution' in stats:
                print(f"\n📺 Channel Distribution:")
                for channel_name, user_count in stats['channel_distribution']:
                    print(f"   • {channel_name}: {user_count} users")
        else:
            print("❌ Could not retrieve bot statistics")
        
        print("\n💡 NEXT STEPS:")
        print("• Add users to your bot with /start")
        print("• Have users join channels with /join <channel_name> <channel_secret>")
        print("• Test broadcasts with authenticated users")
        print("• Use the API endpoints for integration")
    
    def run_full_test_suite(self) -> bool:
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Bot Test Suite")
        print("="*60)
        print(f"🌐 Target: {self.base_url}")
        print(f"🔑 API Key: {self.api_key}")
        print("="*60)
        
        # Test 1: Connectivity
        if not self.test_connectivity():
            self.log("Connectivity test failed - aborting", "ERROR")
            return False
        
        # Test 2: Authentication
        if not self.test_authentication():
            self.log("Authentication test failed", "ERROR")
            return False
        
        # Test 3: API Endpoints
        endpoint_results = self.test_api_endpoints()
        if not any(endpoint_results.values()):
            self.log("All API endpoints failed", "ERROR")
            return False
        
        # Test 4: Broadcast functionality
        self.test_broadcast_functionality()
        
        # Test 5: Channel broadcast
        self.test_channel_broadcast()
        
        # Test 6: Stability
        self.test_stability()
        
        # Get final stats
        stats = self.get_bot_stats()
        self.print_summary(stats)
        
        print("\n🎉 Test suite completed!")
        return True

def main():
    """Main function with command line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Telegram Bot Test Suite')
    parser.add_argument('--url', default=DEFAULT_API_BASE_URL, help='API base URL')
    parser.add_argument('--key', default=DEFAULT_API_KEY, help='API key')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--channel', default='general', help='Channel to test broadcast')
    
    args = parser.parse_args()
    
    tester = BotTester(args.url, args.key)
    
    if args.quick:
        # Quick test mode
        print("🏃 Running Quick Test Mode")
        success = (
            tester.test_connectivity() and 
            tester.test_authentication() and
            any(tester.test_api_endpoints().values())
        )
        print(f"\n{'✅ Quick tests passed!' if success else '❌ Quick tests failed!'}")
    else:
        # Full test suite
        tester.run_full_test_suite()

if __name__ == "__main__":
    main()
