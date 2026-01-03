import requests
import sys
import json
from datetime import datetime

class StickerSwapAPITester:
    def __init__(self, base_url="https://stickertrade-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return {}

    def test_auth_flow(self):
        """Test complete authentication flow"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATION FLOW")
        print("="*50)
        
        # Test send OTP
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        response = self.run_test(
            "Send OTP",
            "POST",
            "auth/send-otp",
            200,
            data={"email": test_email}
        )
        
        if not response:
            return False
            
        # For testing, we'll use a mock OTP since it's logged to console
        # In real testing, you'd check the backend logs for the OTP
        mock_otp = "123456"  # This would need to be retrieved from logs
        
        # Test verify OTP (this will likely fail without real OTP)
        verify_response = self.run_test(
            "Verify OTP (Mock)",
            "POST", 
            "auth/verify-otp",
            400,  # Expecting failure with mock OTP
            data={"email": test_email, "otp": mock_otp}
        )
        
        return True

    def test_groups_flow(self):
        """Test groups functionality"""
        print("\n" + "="*50)
        print("TESTING GROUPS FLOW")
        print("="*50)
        
        if not self.token:
            print("❌ Skipping groups tests - no auth token")
            return False
            
        # Test get groups
        groups = self.run_test(
            "Get Groups",
            "GET",
            "groups",
            200
        )
        
        # Test create group
        group_data = {"name": f"Test Group {datetime.now().strftime('%H%M%S')}"}
        new_group = self.run_test(
            "Create Group",
            "POST",
            "groups",
            200,
            data=group_data
        )
        
        if new_group and 'id' in new_group:
            group_id = new_group['id']
            
            # Test get specific group
            self.run_test(
                "Get Specific Group",
                "GET",
                f"groups/{group_id}",
                200
            )
            
            # Test create invite
            invite_data = {"group_id": group_id, "invited_email": "invite@example.com"}
            self.run_test(
                "Create Invite",
                "POST",
                f"groups/{group_id}/invites",
                200,
                data=invite_data
            )
            
            return group_id
        
        return None

    def test_albums_and_stickers(self, group_id):
        """Test albums and stickers functionality"""
        print("\n" + "="*50)
        print("TESTING ALBUMS & STICKERS")
        print("="*50)
        
        if not group_id:
            print("❌ Skipping albums tests - no group ID")
            return None
            
        # Test get albums
        albums = self.run_test(
            "Get Albums",
            "GET",
            f"albums?group_id={group_id}",
            200
        )
        
        if albums and len(albums) > 0:
            album_id = albums[0]['id']
            
            # Test get stickers
            self.run_test(
                "Get Stickers",
                "GET",
                f"albums/{album_id}/stickers",
                200
            )
            
            # Test get inventory
            self.run_test(
                "Get Inventory",
                "GET",
                f"inventory?album_id={album_id}",
                200
            )
            
            return album_id
        
        return None

    def test_inventory_management(self, album_id):
        """Test inventory management"""
        print("\n" + "="*50)
        print("TESTING INVENTORY MANAGEMENT")
        print("="*50)
        
        if not album_id:
            print("❌ Skipping inventory tests - no album ID")
            return False
            
        # Get stickers first
        stickers_response = self.run_test(
            "Get Stickers for Inventory",
            "GET",
            f"albums/{album_id}/stickers",
            200
        )
        
        if stickers_response and len(stickers_response) > 0:
            sticker_id = stickers_response[0]['id']
            
            # Test update inventory
            self.run_test(
                "Update Inventory",
                "PUT",
                "inventory",
                200,
                data={"sticker_id": sticker_id, "owned_qty": 2}
            )
            
            return True
        
        return False

    def test_matches_and_offers(self, group_id, album_id):
        """Test matches and offers functionality"""
        print("\n" + "="*50)
        print("TESTING MATCHES & OFFERS")
        print("="*50)
        
        if not group_id or not album_id:
            print("❌ Skipping matches/offers tests - missing IDs")
            return False
            
        # Test get matches
        self.run_test(
            "Get Matches",
            "GET",
            f"matches?group_id={group_id}&album_id={album_id}",
            200
        )
        
        # Test get offers
        self.run_test(
            "Get Offers",
            "GET",
            f"offers?group_id={group_id}",
            200
        )
        
        return True

    def test_chat_functionality(self, group_id):
        """Test chat functionality"""
        print("\n" + "="*50)
        print("TESTING CHAT FUNCTIONALITY")
        print("="*50)
        
        if not group_id:
            print("❌ Skipping chat tests - no group ID")
            return False
            
        # Test get chat threads
        self.run_test(
            "Get Chat Threads",
            "GET",
            f"chat/threads?group_id={group_id}",
            200
        )
        
        return True

    def test_notifications(self):
        """Test notifications"""
        print("\n" + "="*50)
        print("TESTING NOTIFICATIONS")
        print("="*50)
        
        if not self.token:
            print("❌ Skipping notifications tests - no auth token")
            return False
            
        # Test get notifications
        self.run_test(
            "Get Notifications",
            "GET",
            "notifications",
            200
        )
        
        return True

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n🚀 Starting StickerSwap API Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Test authentication flow
        self.test_auth_flow()
        
        # For the remaining tests, we need a valid token
        # Since OTP verification requires real OTP from logs, we'll skip authenticated tests
        print("\n⚠️  Note: Authenticated tests skipped - requires real OTP from backend logs")
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = StickerSwapAPITester()
    success = tester.run_all_tests()
    
    # Save test results
    with open('/app/test_reports/backend_api_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'tests_run': tester.tests_run,
            'tests_passed': tester.tests_passed,
            'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            'results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())