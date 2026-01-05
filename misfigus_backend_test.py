import requests
import sys
import json
from datetime import datetime
import time

class MisFigusAPITester:
    def __init__(self, base_url="https://swap-stickers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_email = f"testbackend{datetime.now().strftime('%H%M%S')}@example.com"

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

    def make_request(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Make API request with proper error handling"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"   → {method} {url}")
        if data:
            print(f"   → Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=15)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=15)

            print(f"   ← Status: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"   ← Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   ← Response: {response.text[:200]}")
                response_data = {}

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                if response_data:
                    details += f", Response: {response_data}"
                else:
                    details += f", Response: {response.text[:200]}"

            return success, response_data, details

        except Exception as e:
            return False, {}, f"Exception: {str(e)}"

    def test_authentication_flow(self):
        """Test complete authentication flow with OTP"""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATION FLOW")
        print("="*60)
        
        # Test 1: Send OTP
        print(f"\n🔍 Testing Send OTP for {self.test_email}...")
        success, response_data, details = self.make_request(
            "POST", 
            "auth/send-otp", 
            data={"email": self.test_email},
            expected_status=200
        )
        
        self.log_test("Send OTP", success, details)
        
        if not success or 'dev_otp' not in response_data:
            print("❌ Cannot continue authentication tests - OTP send failed")
            return False
            
        # Extract OTP from response
        otp = response_data['dev_otp']
        print(f"   📧 Got OTP: {otp}")
        
        # Test 2: Verify OTP
        print(f"\n🔍 Testing Verify OTP...")
        success, response_data, details = self.make_request(
            "POST",
            "auth/verify-otp",
            data={"email": self.test_email, "otp": otp},
            expected_status=200
        )
        
        self.log_test("Verify OTP", success, details)
        
        if success and 'token' in response_data:
            self.token = response_data['token']
            self.user_id = response_data['user']['id']
            print(f"   🔑 Got token: {self.token[:20]}...")
            print(f"   👤 User ID: {self.user_id}")
            return True
        
        return False

    def test_albums_functionality(self):
        """Test albums functionality"""
        print("\n" + "="*60)
        print("TESTING ALBUMS FUNCTIONALITY")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping albums tests - no auth token")
            return False
        
        # Test 1: Get Albums List
        print(f"\n🔍 Testing Get Albums...")
        success, albums_data, details = self.make_request(
            "GET",
            "albums",
            expected_status=200
        )
        
        self.log_test("Get Albums", success, details)
        
        if not success or not albums_data:
            print("❌ Cannot continue albums tests - get albums failed")
            return False
        
        # Verify user_state field exists
        has_user_state = all('user_state' in album for album in albums_data)
        self.log_test("Albums have user_state field", has_user_state, 
                     "All albums should have user_state field")
        
        # Find an album to test with
        test_album = None
        for album in albums_data:
            if album.get('status') == 'active':
                test_album = album
                break
        
        if not test_album:
            print("❌ No active album found for testing")
            return False
        
        album_id = test_album['id']
        print(f"   📚 Testing with album: {test_album.get('name', 'Unknown')} (ID: {album_id})")
        
        # Test 2: Activate Album
        print(f"\n🔍 Testing Activate Album...")
        success, activate_data, details = self.make_request(
            "POST",
            f"albums/{album_id}/activate",
            expected_status=200
        )
        
        self.log_test("Activate Album", success, details)
        
        # Test 3: Get Album Details
        print(f"\n🔍 Testing Get Album Details...")
        success, album_details, details = self.make_request(
            "GET",
            f"albums/{album_id}",
            expected_status=200
        )
        
        self.log_test("Get Album Details", success, details)
        
        if success:
            # Verify members list includes user
            members = album_details.get('members', [])
            user_in_members = any(member.get('id') == self.user_id for member in members)
            self.log_test("User in album members list", user_in_members,
                         f"Current user should be in members list. Found {len(members)} members")
        
        # Test 4: Get Albums List Again (verify state change)
        print(f"\n🔍 Testing Get Albums After Activation...")
        success, updated_albums, details = self.make_request(
            "GET",
            "albums",
            expected_status=200
        )
        
        if success:
            activated_album = next((a for a in updated_albums if a['id'] == album_id), None)
            if activated_album:
                is_active = activated_album.get('user_state') == 'active'
                self.log_test("Album state is active after activation", is_active,
                             f"Album user_state: {activated_album.get('user_state')}")
        
        # Test 5: Deactivate Album
        print(f"\n🔍 Testing Deactivate Album...")
        success, deactivate_data, details = self.make_request(
            "DELETE",
            f"albums/{album_id}/deactivate",
            expected_status=200
        )
        
        self.log_test("Deactivate Album", success, details)
        
        # Test 6: Verify Deactivation
        print(f"\n🔍 Testing Get Albums After Deactivation...")
        success, final_albums, details = self.make_request(
            "GET",
            "albums",
            expected_status=200
        )
        
        if success:
            deactivated_album = next((a for a in final_albums if a['id'] == album_id), None)
            if deactivated_album:
                is_inactive = deactivated_album.get('user_state') == 'inactive'
                self.log_test("Album state is inactive after deactivation", is_inactive,
                             f"Album user_state: {deactivated_album.get('user_state')}")
        
        # Test 7: Activate Another Album (if available)
        other_album = None
        for album in albums_data:
            if album.get('status') == 'active' and album['id'] != album_id:
                other_album = album
                break
        
        if other_album:
            other_album_id = other_album['id']
            print(f"\n🔍 Testing Activate Another Album: {other_album.get('name', 'Unknown')}...")
            success, activate_data, details = self.make_request(
                "POST",
                f"albums/{other_album_id}/activate",
                expected_status=200
            )
            
            self.log_test("Activate Another Album", success, details)
            
            if success:
                # Check member count
                success, other_album_details, details = self.make_request(
                    "GET",
                    f"albums/{other_album_id}",
                    expected_status=200
                )
                
                if success:
                    member_count = other_album_details.get('member_count', 0)
                    self.log_test("Album has member count", member_count > 0,
                                 f"Member count: {member_count}")
        
        return True

    def test_error_scenarios(self):
        """Test error scenarios"""
        print("\n" + "="*60)
        print("TESTING ERROR SCENARIOS")
        print("="*60)
        
        # Test 1: Invalid OTP
        print(f"\n🔍 Testing Invalid OTP...")
        success, response_data, details = self.make_request(
            "POST",
            "auth/verify-otp",
            data={"email": self.test_email, "otp": "000000"},
            expected_status=400
        )
        
        self.log_test("Invalid OTP returns 400", success, details)
        
        # Test 2: Access album without authentication
        print(f"\n🔍 Testing Unauthenticated Album Access...")
        old_token = self.token
        self.token = None
        
        success, response_data, details = self.make_request(
            "GET",
            "albums",
            expected_status=401
        )
        
        # We expect this to fail with 401, so success means it properly denied access
        actual_success = success  # We expect this to return 401
        self.log_test("Unauthenticated access denied", actual_success, 
                     "Should deny access without token")
        
        self.token = old_token
        
        # Test 3: Access non-existent album
        if self.token:
            print(f"\n🔍 Testing Non-existent Album Access...")
            success, response_data, details = self.make_request(
                "GET",
                "albums/non-existent-album-id",
                expected_status=403  # or 404
            )
            
            # We expect this to fail with 403 or 404, so success means it properly denied access
            actual_success = success  # We expect this to return 403/404
            self.log_test("Non-existent album access denied", actual_success,
                         "Should return error for non-existent album")

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n🚀 Starting MisFigus Sticker Trading App API Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test Email: {self.test_email}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=10)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Run test suites
        auth_success = self.test_authentication_flow()
        
        if auth_success:
            self.test_albums_functionality()
        else:
            print("⚠️  Skipping albums tests - authentication failed")
        
        self.test_error_scenarios()
        
        # Print summary
        print(f"\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        success_rate = (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = MisFigusAPITester()
    success = tester.run_all_tests()
    
    # Save test results
    try:
        import os
        os.makedirs('/app/test_reports', exist_ok=True)
        with open('/app/test_reports/misfigus_backend_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'tests_run': tester.tests_run,
                'tests_passed': tester.tests_passed,
                'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
                'results': tester.test_results
            }, f, indent=2)
        print(f"\n📄 Test results saved to /app/test_reports/misfigus_backend_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())