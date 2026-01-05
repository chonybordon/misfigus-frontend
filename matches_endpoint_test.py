import requests
import sys
import json
from datetime import datetime

class MatchesEndpointTester:
    def __init__(self, base_url="https://swap-stickers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = "3b6734a6-4a17-437f-845f-ba265fcc4b7b"  # Test user ID provided
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test albums provided in the review request
        self.fifa_album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"  # FIFA World Cup Qatar 2022 (has matches)
        self.pokemon_album_id = "ecc59406-6ec2-4c32-b721-8d50bd04a89e"  # Pokémon (likely no matches)

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
            
            if response.status_code == expected_status:
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

    def test_auth_flow(self):
        """Test authentication with real email"""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATION FLOW")
        print("="*60)
        
        # Use a real-looking email for testing
        test_email = f"matches.test.{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com"
        
        print(f"🔍 Testing OTP flow with email: {test_email}")
        
        # Send OTP
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": test_email},
            200
        )
        
        self.log_test("Send OTP", success, str(response) if not success else "")
        
        if not success:
            return False
            
        # Check backend logs for OTP
        print("\n📋 Checking backend logs for OTP...")
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            log_lines = result.stdout.split('\n')
            otp_code = None
            
            # Look for the most recent OTP for our test email
            for line in reversed(log_lines):
                if "[OTP] OTP:" in line:
                    # Extract OTP from log line
                    parts = line.split("[OTP] OTP:")
                    if len(parts) > 1:
                        otp_code = parts[1].strip()
                        break
            
            if otp_code:
                print(f"✅ Found OTP in logs: {otp_code}")
                
                # Verify OTP
                success, response = self.make_request(
                    "POST",
                    "auth/verify-otp",
                    {"email": test_email, "otp": otp_code},
                    200
                )
                
                self.log_test("Verify OTP", success, str(response) if not success else "")
                
                if success and 'token' in response:
                    self.token = response['token']
                    self.user_id = response['user']['id']
                    print(f"✅ Authentication successful! User ID: {self.user_id}")
                    return True
                    
            else:
                print("❌ Could not find OTP in backend logs")
                self.log_test("Extract OTP from logs", False, "OTP not found in logs")
                
        except Exception as e:
            print(f"❌ Error checking logs: {e}")
            self.log_test("Check backend logs", False, str(e))
            
        return False

    def test_correct_matches_endpoint(self):
        """Test the CORRECT endpoint: GET /api/albums/{album_id}/matches"""
        print("\n" + "="*60)
        print("TESTING CORRECT MATCHES ENDPOINT")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping matches test - no auth token")
            return False

        # Test 1: FIFA World Cup Qatar 2022 (should have matches or empty array)
        print(f"\n🔍 Testing FIFA World Cup Qatar 2022: {self.fifa_album_id}")
        success, response = self.make_request(
            "GET", 
            f"albums/{self.fifa_album_id}/matches", 
            expected_status=200
        )
        
        if success:
            self.log_test(
                "FIFA album matches endpoint returns 200", 
                True,
                f"Returned {len(response)} matches"
            )
            
            # Verify response is an array
            is_array = isinstance(response, list)
            self.log_test(
                "FIFA album matches returns array", 
                is_array,
                f"Response type: {type(response)}"
            )
            
            # If there are matches, verify structure
            if response and len(response) > 0:
                first_match = response[0]
                required_fields = ['user', 'has_stickers_i_need', 'needs_stickers_i_have', 'can_exchange']
                has_required_fields = all(field in first_match for field in required_fields)
                self.log_test(
                    "FIFA album match has required fields", 
                    has_required_fields,
                    f"Match structure: {list(first_match.keys()) if isinstance(first_match, dict) else 'Not a dict'}"
                )
        else:
            self.log_test("FIFA album matches endpoint returns 200", False, response)

        # Test 2: Pokémon album (likely no matches, but should still return 200 with empty array)
        print(f"\n🔍 Testing Pokémon album: {self.pokemon_album_id}")
        success, response = self.make_request(
            "GET", 
            f"albums/{self.pokemon_album_id}/matches", 
            expected_status=200
        )
        
        if success:
            self.log_test(
                "Pokémon album matches endpoint returns 200", 
                True,
                f"Returned {len(response)} matches"
            )
            
            # Verify response is an array (even if empty)
            is_array = isinstance(response, list)
            self.log_test(
                "Pokémon album matches returns array", 
                is_array,
                f"Response type: {type(response)}"
            )
        else:
            self.log_test("Pokémon album matches endpoint returns 200", False, response)

        return True

    def test_incorrect_matches_endpoint(self):
        """Test the OLD incorrect endpoint: GET /api/matches?album_id={album_id}"""
        print("\n" + "="*60)
        print("TESTING INCORRECT MATCHES ENDPOINT (SHOULD RETURN 404)")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping incorrect endpoint test - no auth token")
            return False

        # Test 1: FIFA World Cup Qatar 2022 with old endpoint (should return 404)
        print(f"\n🔍 Testing old endpoint with FIFA album: {self.fifa_album_id}")
        success, response = self.make_request(
            "GET", 
            f"matches?album_id={self.fifa_album_id}", 
            expected_status=404
        )
        
        self.log_test(
            "Old FIFA endpoint returns 404", 
            success,  # Success means we got the expected 404
            f"Correctly returned 404: {response}"
        )

        # Test 2: Pokémon album with old endpoint (should return 404)
        print(f"\n🔍 Testing old endpoint with Pokémon album: {self.pokemon_album_id}")
        success, response = self.make_request(
            "GET", 
            f"matches?album_id={self.pokemon_album_id}", 
            expected_status=404
        )
        
        self.log_test(
            "Old Pokémon endpoint returns 404", 
            success,  # Success means we got the expected 404
            f"Correctly returned 404: {response}"
        )

        return True

    def test_album_activation_for_matches(self):
        """Activate albums to ensure we can test matches properly"""
        print("\n" + "="*60)
        print("TESTING ALBUM ACTIVATION FOR MATCHES")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping activation test - no auth token")
            return False

        # Try to activate FIFA album
        success, response = self.make_request(
            "POST", 
            f"albums/{self.fifa_album_id}/activate", 
            expected_status=200
        )
        
        if success:
            self.log_test("FIFA album activation", True, "Album activated successfully")
        else:
            # Check if it's already activated (400 error is expected)
            if "already activated" in str(response).lower():
                self.log_test("FIFA album activation", True, "Album already activated")
            else:
                self.log_test("FIFA album activation", False, response)

        # Try to activate Pokémon album
        success, response = self.make_request(
            "POST", 
            f"albums/{self.pokemon_album_id}/activate", 
            expected_status=200
        )
        
        if success:
            self.log_test("Pokémon album activation", True, "Album activated successfully")
        else:
            # Check if it's already activated (400 error is expected)
            if "already activated" in str(response).lower():
                self.log_test("Pokémon album activation", True, "Album already activated")
            else:
                self.log_test("Pokémon album activation", False, response)

        return True

    def test_matches_without_activation(self):
        """Test matches endpoint without album activation (should return 403)"""
        print("\n" + "="*60)
        print("TESTING MATCHES WITHOUT ACTIVATION")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping non-activation test - no auth token")
            return False

        # Use a different album ID that we haven't activated
        fake_album_id = "00000000-0000-0000-0000-000000000000"
        
        success, response = self.make_request(
            "GET", 
            f"albums/{fake_album_id}/matches", 
            expected_status=403
        )
        
        self.log_test(
            "Non-activated album returns 403", 
            success,  # Success means we got the expected 403
            f"Correctly returned 403: {response}"
        )

        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n🚀 Starting Matches Endpoint Bug Fix Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"FIFA Album ID: {self.fifa_album_id}")
        print(f"Pokémon Album ID: {self.pokemon_album_id}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Run test sequence
        tests = [
            ("Authentication Flow", self.test_auth_flow),
            ("Album Activation", self.test_album_activation_for_matches),
            ("Correct Matches Endpoint", self.test_correct_matches_endpoint),
            ("Incorrect Matches Endpoint", self.test_incorrect_matches_endpoint),
            ("Matches Without Activation", self.test_matches_without_activation)
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
    tester = MatchesEndpointTester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'matches_endpoint_bug_fix',
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'fifa_album_id': tester.fifa_album_id,
        'pokemon_album_id': tester.pokemon_album_id,
        'token_obtained': tester.token is not None
    }
    
    try:
        with open('/app/matches_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/matches_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())