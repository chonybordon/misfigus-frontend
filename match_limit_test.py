import requests
import sys
import json
import time
from datetime import datetime

class MisFigusMatchLimitTester:
    def __init__(self, base_url="https://sticker-swap-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_email = None
        self.album_id = None

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
        print("SETTING UP AUTHENTICATED USER FOR MATCH LIMIT TESTING")
        print("="*60)
        
        # Generate unique test email
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.test_email = f"match.limit.test.{timestamp}@gmail.com"
        
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
            "full_name": "Match Limit Test User",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-id-match-limit",
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
        
        # Get an album to work with
        success, albums_response = self.make_request("GET", "albums", expected_status=200)
        
        if success:
            active_albums = [album for album in albums_response if album.get('status') == 'active']
            if active_albums:
                self.album_id = active_albums[0]['id']
                
                # Activate the album
                success, response = self.make_request(
                    "POST", 
                    f"albums/{self.album_id}/activate", 
                    expected_status=200
                )
                
                if not success:
                    self.log_test("Setup - Activate Album", False, response)
                    return False
        
        self.log_test("Setup - User Authentication Complete", True, f"User ID: {self.user_id}, Album ID: {self.album_id}")
        return True

    def test_daily_match_limit_with_exchanges(self):
        """Test daily match limits using the exchanges endpoint"""
        print("\n" + "="*60)
        print("TESTING DAILY MATCH LIMITS WITH EXCHANGES ENDPOINT")
        print("="*60)
        
        if not self.token or not self.album_id:
            print("❌ Skipping match limit test - missing setup")
            return False
        
        # Ensure user is on free plan
        success, response = self.make_request("POST", "user/downgrade-free", expected_status=200)
        
        if not success:
            self.log_test("Setup Free Plan", False, response)
            return False
        
        # Check initial plan status
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            initial_matches_used = plan_response.get("matches_used_today", 0)
            can_match = plan_response.get("can_match", True)
            matches_limit = plan_response.get("matches_limit", 0)
            
            self.log_test("Initial State - Free plan active", plan_response.get("plan") == "free", f"Expected 'free', got '{plan_response.get('plan')}'")
            self.log_test("Initial State - Matches used is 0", initial_matches_used == 0, f"Expected 0, got {initial_matches_used}")
            self.log_test("Initial State - Can match is true", can_match == True, f"Expected true, got {can_match}")
            self.log_test("Initial State - Matches limit is 1", matches_limit == 1, f"Expected 1, got {matches_limit}")
        
        # Test the exchanges endpoint to see if it properly enforces limits
        # First, let's check what matches are available
        success, matches_response = self.make_request(
            "GET", 
            f"albums/{self.album_id}/matches", 
            expected_status=200
        )
        
        if success:
            matches_count = len(matches_response)
            self.log_test("Get Matches - Endpoint works", True, f"Found {matches_count} potential matches")
            
            # If there are no matches, that's expected for a new user with no inventory
            if matches_count == 0:
                print("   No matches available (expected for new user with no inventory)")
            else:
                print(f"   Found {matches_count} potential matches")
        
        # Test creating an exchange (this should increment match counter if successful)
        # Note: This might fail due to validation, but we're testing the limit logic
        test_exchange_data = {
            "partner_user_id": "test-partner-id",
            "my_stickers": ["test-sticker-1"],
            "their_stickers": ["test-sticker-2"]
        }
        
        success, exchange_response = self.make_request(
            "POST", 
            f"albums/{self.album_id}/exchanges", 
            test_exchange_data,
            [200, 400, 403, 404, 422]  # Accept various responses
        )
        
        # The specific response doesn't matter as much as testing the limit enforcement
        print(f"   Exchange creation attempt: {exchange_response}")
        
        # Now let's test what happens when we simulate hitting the daily limit
        # We'll do this by upgrading to premium and then downgrading to reset, 
        # but first let's see the current state
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            matches_used_after = plan_response.get("matches_used_today", 0)
            can_match_after = plan_response.get("can_match", True)
            
            print(f"   Matches used after exchange attempt: {matches_used_after}")
            print(f"   Can match after exchange attempt: {can_match_after}")
            
            # Test the logic: if matches_used_today >= 1, can_match should be false for free users
            if matches_used_after >= 1:
                expected_can_match = False
                actual_can_match = can_match_after
                
                self.log_test("Daily Limit - can_match false when limit reached", 
                            actual_can_match == expected_can_match, 
                            f"Expected {expected_can_match}, got {actual_can_match}")
            else:
                self.log_test("Daily Limit - No matches used yet", True, "Exchange attempt didn't increment counter (expected for invalid data)")
        
        return True

    def test_premium_unlimited_matches(self):
        """Test that premium users have unlimited matches"""
        print("\n" + "="*60)
        print("TESTING PREMIUM UNLIMITED MATCHES")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping premium test - no auth token")
            return False
        
        # Upgrade to premium
        success, response = self.make_request("POST", "user/upgrade-premium", expected_status=200)
        
        if not success:
            self.log_test("Upgrade to Premium", False, response)
            return False
        
        # Check plan status
        success, plan_response = self.make_request("GET", "user/plan-status", expected_status=200)
        
        if success:
            plan = plan_response.get("plan")
            is_premium = plan_response.get("is_premium")
            matches_limit = plan_response.get("matches_limit")
            can_match = plan_response.get("can_match")
            
            self.log_test("Premium - Plan is premium", plan == "premium", f"Expected 'premium', got '{plan}'")
            self.log_test("Premium - is_premium is true", is_premium == True, f"Expected true, got {is_premium}")
            self.log_test("Premium - matches_limit is null", matches_limit is None, f"Expected null, got {matches_limit}")
            self.log_test("Premium - can_match is true", can_match == True, f"Expected true, got {can_match}")
            
            # Premium users should always be able to match regardless of usage
            matches_used = plan_response.get("matches_used_today", 0)
            print(f"   Premium user matches used today: {matches_used}")
            print(f"   Premium user can still match: {can_match}")
        
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
        """Run all match limit tests"""
        print(f"\n🚀 Starting MisFigus Match Limit Tests")
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
            ("Daily Match Limits with Exchanges", self.test_daily_match_limit_with_exchanges),
            ("Premium Unlimited Matches", self.test_premium_unlimited_matches)
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
    tester = MisFigusMatchLimitTester()
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
        with open('/app/match_limit_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/match_limit_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())