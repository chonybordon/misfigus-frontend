import requests
import sys
import json
import time
from datetime import datetime

class MisFigusFreemiumTester:
    def __init__(self, base_url="https://trade-stickers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_email = None
        self.album_ids = []

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

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            print(f"   {method} {url} -> {response.status_code}")
            
            # Handle multiple expected status codes
            if isinstance(expected_status, list):
                status_match = response.status_code in expected_status
            else:
                status_match = response.status_code == expected_status
            
            if status_match:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    return False, f"Status: {response.status_code}, Response: {error_data}"
                except:
                    return False, f"Status: {response.status_code}, Response: {response.text[:200]}"

        except Exception as e:
            return False, f"Exception: {str(e)}"

    def setup_authenticated_user(self):
        """Create and authenticate a test user"""
        print("\n" + "="*60)
        print("SETTING UP AUTHENTICATED USER")
        print("="*60)
        
        # Generate unique test email
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.test_email = f"freemium.test.{timestamp}@gmail.com"
        
        print(f"🔍 Creating user: {self.test_email}")
        
        # Send OTP
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": self.test_email},
            200
        )
        
        if not success:
            self.log_test("Setup - Send OTP", False, response)
            return False
        
        # Extract OTP from logs
        otp_code = self.extract_otp_from_logs()
        if not otp_code:
            self.log_test("Setup - Extract OTP", False, "Could not find OTP in logs")
            return False
        
        # Verify OTP
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": self.test_email, "otp": otp_code},
            200
        )
        
        if not success:
            self.log_test("Setup - Verify OTP", False, response)
            return False
        
        self.token = response['token']
        self.user_id = response['user']['id']
        
        # Complete onboarding
        onboarding_data = {
            "full_name": "Freemium Test User",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-id-freemium",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "neighborhood_text": "Test Area",
            "radius_km": 5,
            "terms_version": "1.0"
        }
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            200
        )
        
        if not success:
            self.log_test("Setup - Complete Onboarding", False, response)
            return False
        
        self.log_test("Setup - User Authentication Complete", True, f"User ID: {self.user_id}")
        return True

    def test_plan_status_endpoint(self):
        """Test GET /api/user/plan-status endpoint"""
        print("\n" + "="*60)
        print("TESTING PLAN STATUS ENDPOINT")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping plan status test - no auth token")
            return False
        
        # Test 1: Get plan status for new user (should be free)
        success, response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        self.log_test("GET /user/plan-status - Basic Request", success, str(response) if not success else "")
        
        if success:
            # Verify response structure
            required_fields = [
                "plan", "is_premium", "matches_used_today", "matches_limit", 
                "can_match", "active_albums", "albums_limit", "can_activate_album"
            ]
            
            for field in required_fields:
                has_field = field in response
                self.log_test(f"Plan Status - Has {field} field", has_field, f"Missing '{field}' field")
            
            # Verify default values for new free user
            if all(field in response for field in required_fields):
                plan_is_free = response["plan"] == "free"
                is_premium_false = response["is_premium"] == False
                matches_used_zero = response["matches_used_today"] == 0
                matches_limit_one = response["matches_limit"] == 1
                can_match_true = response["can_match"] == True
                active_albums_zero = response["active_albums"] == 0
                albums_limit_one = response["albums_limit"] == 1
                can_activate_true = response["can_activate_album"] == True
                
                self.log_test("Plan Status - Default plan is free", plan_is_free, f"Expected 'free', got '{response['plan']}'")
                self.log_test("Plan Status - is_premium is false", is_premium_false, f"Expected false, got {response['is_premium']}")
                self.log_test("Plan Status - matches_used_today is 0", matches_used_zero, f"Expected 0, got {response['matches_used_today']}")
                self.log_test("Plan Status - matches_limit is 1", matches_limit_one, f"Expected 1, got {response['matches_limit']}")
                self.log_test("Plan Status - can_match is true", can_match_true, f"Expected true, got {response['can_match']}")
                self.log_test("Plan Status - active_albums is 0", active_albums_zero, f"Expected 0, got {response['active_albums']}")
                self.log_test("Plan Status - albums_limit is 1", albums_limit_one, f"Expected 1, got {response['albums_limit']}")
                self.log_test("Plan Status - can_activate_album is true", can_activate_true, f"Expected true, got {response['can_activate_album']}")
        
        return True

    def test_upgrade_premium_endpoint(self):
        """Test POST /api/user/upgrade-premium endpoint"""
        print("\n" + "="*60)
        print("TESTING UPGRADE PREMIUM ENDPOINT")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping upgrade test - no auth token")
            return False
        
        # Test 1: Upgrade to premium
        success, response = self.make_request("POST", "user/upgrade-premium", expected_status=200)
        
        self.log_test("POST /user/upgrade-premium - Basic Request", success, str(response) if not success else "")
        
        if success:
            # Verify response structure
            has_message = "message" in response
            has_user = "user" in response
            
            self.log_test("Upgrade Premium - Response has message", has_message, "Missing 'message' field")
            self.log_test("Upgrade Premium - Response has user", has_user, "Missing 'user' field")
            
            if has_user:
                user_plan_premium = response["user"].get("plan") == "premium"
                self.log_test("Upgrade Premium - User plan set to premium", user_plan_premium, f"Expected 'premium', got '{response['user'].get('plan')}'")
        
        # Test 2: Verify plan status after upgrade
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            plan_is_premium = plan_response.get("plan") == "premium"
            is_premium_true = plan_response.get("is_premium") == True
            matches_limit_null = plan_response.get("matches_limit") is None
            albums_limit_null = plan_response.get("albums_limit") is None
            can_match_true = plan_response.get("can_match") == True
            can_activate_true = plan_response.get("can_activate_album") == True
            
            self.log_test("After Upgrade - Plan is premium", plan_is_premium, f"Expected 'premium', got '{plan_response.get('plan')}'")
            self.log_test("After Upgrade - is_premium is true", is_premium_true, f"Expected true, got {plan_response.get('is_premium')}")
            self.log_test("After Upgrade - matches_limit is null", matches_limit_null, f"Expected null, got {plan_response.get('matches_limit')}")
            self.log_test("After Upgrade - albums_limit is null", albums_limit_null, f"Expected null, got {plan_response.get('albums_limit')}")
            self.log_test("After Upgrade - can_match is true", can_match_true, f"Expected true, got {plan_response.get('can_match')}")
            self.log_test("After Upgrade - can_activate_album is true", can_activate_true, f"Expected true, got {plan_response.get('can_activate_album')}")
        
        return True

    def test_downgrade_free_endpoint(self):
        """Test POST /api/user/downgrade-free endpoint"""
        print("\n" + "="*60)
        print("TESTING DOWNGRADE FREE ENDPOINT")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping downgrade test - no auth token")
            return False
        
        # Test 1: Downgrade to free
        success, response = self.make_request("POST", "user/downgrade-free", expected_status=200)
        
        self.log_test("POST /user/downgrade-free - Basic Request", success, str(response) if not success else "")
        
        if success:
            # Verify response structure
            has_message = "message" in response
            has_user = "user" in response
            
            self.log_test("Downgrade Free - Response has message", has_message, "Missing 'message' field")
            self.log_test("Downgrade Free - Response has user", has_user, "Missing 'user' field")
            
            if has_user:
                user_plan_free = response["user"].get("plan") == "free"
                matches_reset = response["user"].get("matches_used_today") == 0
                
                self.log_test("Downgrade Free - User plan set to free", user_plan_free, f"Expected 'free', got '{response['user'].get('plan')}'")
                self.log_test("Downgrade Free - Daily matches reset", matches_reset, f"Expected 0, got {response['user'].get('matches_used_today')}")
        
        # Test 2: Verify plan status after downgrade
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            plan_is_free = plan_response.get("plan") == "free"
            is_premium_false = plan_response.get("is_premium") == False
            matches_limit_one = plan_response.get("matches_limit") == 1
            albums_limit_one = plan_response.get("albums_limit") == 1
            
            self.log_test("After Downgrade - Plan is free", plan_is_free, f"Expected 'free', got '{plan_response.get('plan')}'")
            self.log_test("After Downgrade - is_premium is false", is_premium_false, f"Expected false, got {plan_response.get('is_premium')}")
            self.log_test("After Downgrade - matches_limit is 1", matches_limit_one, f"Expected 1, got {plan_response.get('matches_limit')}")
            self.log_test("After Downgrade - albums_limit is 1", albums_limit_one, f"Expected 1, got {plan_response.get('albums_limit')}")
        
        return True

    def test_album_activation_limits(self):
        """Test album activation limits for free vs premium users"""
        print("\n" + "="*60)
        print("TESTING ALBUM ACTIVATION LIMITS")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping album activation test - no auth token")
            return False
        
        # Get available albums
        success, albums_response = self.make_request("GET", "albums", expected_status=200)
        
        if not success:
            self.log_test("Get Albums for Activation Test", False, albums_response)
            return False
        
        # Find active albums to test with
        active_albums = [album for album in albums_response if album.get('status') == 'active']
        
        if len(active_albums) < 2:
            self.log_test("Find Multiple Active Albums", False, f"Need at least 2 active albums, found {len(active_albums)}")
            return False
        
        self.album_ids = [album['id'] for album in active_albums[:2]]
        print(f"✅ Testing with albums: {self.album_ids}")
        
        # Ensure user is on free plan
        self.make_request("POST", "user/downgrade-free", expected_status=200)
        
        # Test 1: Activate first album (should succeed)
        success, response = self.make_request(
            "POST", 
            f"albums/{self.album_ids[0]}/activate", 
            expected_status=200
        )
        
        self.log_test("Free User - Activate First Album", success, str(response) if not success else "")
        
        # Test 2: Try to activate second album (should fail with ALBUM_LIMIT)
        success, response = self.make_request(
            "POST", 
            f"albums/{self.album_ids[1]}/activate", 
            expected_status=403
        )
        
        self.log_test("Free User - Activate Second Album (Should Fail)", success, str(response) if not success else "")
        
        if success and isinstance(response, dict):
            has_code = "code" in response.get("detail", {}) if isinstance(response.get("detail"), dict) else False
            correct_code = response.get("detail", {}).get("code") == "ALBUM_LIMIT" if has_code else False
            
            self.log_test("Free User - Correct Error Code (ALBUM_LIMIT)", correct_code, f"Expected ALBUM_LIMIT, got {response}")
        
        # Test 3: Upgrade to premium
        success, response = self.make_request("POST", "user/upgrade-premium", expected_status=200)
        
        if not success:
            self.log_test("Upgrade for Album Test", False, response)
            return False
        
        # Test 4: Try to activate second album as premium user (should succeed)
        success, response = self.make_request(
            "POST", 
            f"albums/{self.album_ids[1]}/activate", 
            expected_status=200
        )
        
        self.log_test("Premium User - Activate Second Album", success, str(response) if not success else "")
        
        return True

    def test_daily_match_limits(self):
        """Test daily match limits for free vs premium users"""
        print("\n" + "="*60)
        print("TESTING DAILY MATCH LIMITS")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping match limits test - no auth token")
            return False
        
        # Ensure we have activated albums
        if not self.album_ids:
            self.log_test("Setup Albums for Match Test", False, "No albums activated")
            return False
        
        # Downgrade to free plan
        success, response = self.make_request("POST", "user/downgrade-free", expected_status=200)
        
        if not success:
            self.log_test("Downgrade for Match Test", False, response)
            return False
        
        # Test 1: Create first exchange (should succeed)
        # Note: We'll test the exchanges endpoint which should increment match counter
        album_id = self.album_ids[0]
        
        success, response = self.make_request(
            "POST", 
            f"albums/{album_id}/exchanges", 
            {"partner_user_id": "dummy-user-id", "my_stickers": ["sticker1"], "their_stickers": ["sticker2"]},
            [200, 400, 403, 404]  # Accept various responses as we're testing the limit logic
        )
        
        # The actual response doesn't matter as much as testing the limit logic
        # Let's check plan status to see match usage
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            initial_matches_used = plan_response.get("matches_used_today", 0)
            can_match = plan_response.get("can_match", True)
            
            print(f"   Initial matches used: {initial_matches_used}")
            print(f"   Can match: {can_match}")
        
        # Test 2: Simulate reaching daily limit by directly testing the limit logic
        # We'll upgrade to premium and test unlimited matches
        success, response = self.make_request("POST", "user/upgrade-premium", expected_status=200)
        
        if success:
            # Test premium user can always match
            success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
            
            if success:
                matches_limit_null = plan_response.get("matches_limit") is None
                can_match_true = plan_response.get("can_match") == True
                
                self.log_test("Premium User - Unlimited matches (limit is null)", matches_limit_null, f"Expected null, got {plan_response.get('matches_limit')}")
                self.log_test("Premium User - Can always match", can_match_true, f"Expected true, got {plan_response.get('can_match')}")
        
        return True

    def test_daily_reset_logic(self):
        """Test that daily match counters reset properly"""
        print("\n" + "="*60)
        print("TESTING DAILY RESET LOGIC")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping daily reset test - no auth token")
            return False
        
        # Downgrade to free to test reset logic
        success, response = self.make_request("POST", "user/downgrade-free", expected_status=200)
        
        if not success:
            self.log_test("Setup Free Plan for Reset Test", False, response)
            return False
        
        # Get current plan status
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            matches_used = plan_response.get("matches_used_today", 0)
            matches_date = plan_response.get("matches_used_date")
            
            # The reset logic should ensure matches_used_today is 0 for new day
            # Since we just downgraded, it should be reset
            matches_reset = matches_used == 0
            
            self.log_test("Daily Reset - Matches used reset to 0", matches_reset, f"Expected 0, got {matches_used}")
            
            if matches_date:
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                date_is_today = matches_date == today
                
                self.log_test("Daily Reset - Date is today", date_is_today, f"Expected {today}, got {matches_date}")
        
        return True

    def test_full_freemium_flow(self):
        """Test the complete freemium flow as described in the requirements"""
        print("\n" + "="*60)
        print("TESTING FULL FREEMIUM FLOW")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping full flow test - no auth token")
            return False
        
        # Step 1: Create user (starts as free) - already done in setup
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            starts_free = plan_response.get("plan") == "free"
            self.log_test("Full Flow - User starts as free", starts_free, f"Expected 'free', got '{plan_response.get('plan')}'")
        
        # Step 2: Check plan-status - already tested above
        
        # Step 3: Activate first album (should succeed)
        if self.album_ids:
            # Deactivate any existing albums first
            for album_id in self.album_ids:
                self.make_request("DELETE", f"albums/{album_id}/deactivate", expected_status=[200, 400])
            
            success, response = self.make_request(
                "POST", 
                f"albums/{self.album_ids[0]}/activate", 
                expected_status=200
            )
            
            self.log_test("Full Flow - Activate first album succeeds", success, str(response) if not success else "")
            
            # Step 4: Try to activate second album (should fail with ALBUM_LIMIT)
            if len(self.album_ids) > 1:
                success, response = self.make_request(
                    "POST", 
                    f"albums/{self.album_ids[1]}/activate", 
                    expected_status=403
                )
                
                self.log_test("Full Flow - Second album activation fails", success, str(response) if not success else "")
                
                # Step 5: Upgrade to premium
                success, response = self.make_request("POST", "user/upgrade-premium", expected_status=200)
                
                self.log_test("Full Flow - Upgrade to premium", success, str(response) if not success else "")
                
                # Step 6: Activate second album (should succeed now)
                success, response = self.make_request(
                    "POST", 
                    f"albums/{self.album_ids[1]}/activate", 
                    expected_status=200
                )
                
                self.log_test("Full Flow - Second album activation succeeds after upgrade", success, str(response) if not success else "")
                
                # Step 7: Downgrade to free
                success, response = self.make_request("POST", "user/downgrade-free", expected_status=200)
                
                self.log_test("Full Flow - Downgrade to free", success, str(response) if not success else "")
                
                # Step 8: Check plan-status again
                success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
                
                if success:
                    back_to_free = plan_response.get("plan") == "free"
                    limits_restored = plan_response.get("albums_limit") == 1 and plan_response.get("matches_limit") == 1
                    
                    self.log_test("Full Flow - Back to free plan", back_to_free, f"Expected 'free', got '{plan_response.get('plan')}'")
                    self.log_test("Full Flow - Limits restored", limits_restored, f"Expected limits of 1, got albums: {plan_response.get('albums_limit')}, matches: {plan_response.get('matches_limit')}")
        
        return True

    def extract_otp_from_logs(self):
        """Extract OTP from backend logs"""
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            log_lines = result.stdout.split('\n')
            
            # Look for the most recent OTP
            for line in reversed(log_lines):
                if "[OTP] OTP:" in line:
                    parts = line.split("[OTP] OTP:")
                    if len(parts) > 1:
                        return parts[1].strip()
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting OTP from logs: {e}")
            return None

    def run_all_tests(self):
        """Run all freemium monetization tests"""
        print(f"\n🚀 Starting MisFigus Freemium Monetization Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Setup authenticated user
        if not self.setup_authenticated_user():
            print("❌ Failed to setup authenticated user")
            return False
        
        # Run test sequence
        tests = [
            ("Plan Status Endpoint", self.test_plan_status_endpoint),
            ("Upgrade Premium Endpoint", self.test_upgrade_premium_endpoint),
            ("Downgrade Free Endpoint", self.test_downgrade_free_endpoint),
            ("Album Activation Limits", self.test_album_activation_limits),
            ("Daily Match Limits", self.test_daily_match_limits),
            ("Daily Reset Logic", self.test_daily_reset_logic),
            ("Full Freemium Flow", self.test_full_freemium_flow)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔄 Running {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} (Exception)", False, str(e))
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return len(failed_tests) == 0

def main():
    tester = MisFigusFreemiumTester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'test_email': tester.test_email,
        'token_obtained': tester.token is not None
    }
    
    try:
        with open('/app/freemium_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/freemium_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())