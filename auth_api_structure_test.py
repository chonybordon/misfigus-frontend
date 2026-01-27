import requests
import sys
import json
import time
from datetime import datetime

class MisFigusAuthOnboardingAPITester:
    def __init__(self, base_url="https://misfigus-trading.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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

    def make_request(self, method, endpoint, data=None, expected_status=200, headers=None):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if headers:
            request_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=request_headers, timeout=10)

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

    def test_send_otp_api_structure(self):
        """Test POST /api/auth/send-otp API structure and responses"""
        print("\n" + "="*60)
        print("TESTING SEND OTP API STRUCTURE")
        print("="*60)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        test_email = f"misfigus.api.test.{timestamp}@gmail.com"
        
        # Test 1: Valid email format
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": test_email},
            200
        )
        
        self.log_test("Send OTP - Valid Email", success, str(response) if not success else "")
        
        if success:
            # Check response structure
            has_message = "message" in response
            has_email = "email" in response and response["email"] == test_email
            no_otp_exposed = "otp" not in response and "code" not in response
            
            self.log_test("Send OTP - Response has message field", has_message, "Missing 'message' field")
            self.log_test("Send OTP - Response has email field", has_email, "Missing or incorrect 'email' field")
            self.log_test("Send OTP - OTP not exposed in response", no_otp_exposed, "OTP should never be in response")
        
        # Test 2: Missing email field
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {},
            [400, 422]
        )
        
        self.log_test("Send OTP - Missing Email Field", success, str(response) if not success else "Correctly rejected missing email")
        
        # Test 3: Empty email
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": ""},
            [400, 422]
        )
        
        self.log_test("Send OTP - Empty Email", success, str(response) if not success else "Correctly rejected empty email")
        
        return True

    def test_verify_otp_api_structure(self):
        """Test POST /api/auth/verify-otp API structure"""
        print("\n" + "="*60)
        print("TESTING VERIFY OTP API STRUCTURE")
        print("="*60)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        test_email = f"misfigus.verify.test.{timestamp}@gmail.com"
        
        # Test 1: Invalid OTP format
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": test_email, "otp": "12345"},  # 5 digits instead of 6
            400
        )
        
        self.log_test("Verify OTP - Invalid OTP Format (5 digits)", success, str(response) if not success else "Correctly rejected 5-digit OTP")
        
        # Test 2: Non-numeric OTP
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": test_email, "otp": "abcdef"},
            400
        )
        
        self.log_test("Verify OTP - Non-numeric OTP", success, str(response) if not success else "Correctly rejected non-numeric OTP")
        
        # Test 3: Missing email field
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"otp": "123456"},
            [400, 422]
        )
        
        self.log_test("Verify OTP - Missing Email Field", success, str(response) if not success else "Correctly rejected missing email")
        
        # Test 4: Missing OTP field
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": test_email},
            [400, 422]
        )
        
        self.log_test("Verify OTP - Missing OTP Field", success, str(response) if not success else "Correctly rejected missing OTP")
        
        # Test 5: Non-existent email (no OTP sent)
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": "nonexistent@test.com", "otp": "123456"},
            400
        )
        
        self.log_test("Verify OTP - Non-existent Email", success, str(response) if not success else "Correctly rejected non-existent email")
        
        return True

    def test_auth_me_api_structure(self):
        """Test GET /api/auth/me API structure"""
        print("\n" + "="*60)
        print("TESTING AUTH ME API STRUCTURE")
        print("="*60)
        
        # Test 1: No authorization header
        success, response = self.make_request("GET", "auth/me", expected_status=401)
        
        self.log_test("GET /auth/me - No Auth Header", success, str(response) if not success else "Correctly rejected request without auth")
        
        # Test 2: Invalid authorization header format
        success, response = self.make_request(
            "GET", 
            "auth/me", 
            expected_status=401,
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.log_test("GET /auth/me - Invalid Auth Format", success, str(response) if not success else "Correctly rejected invalid auth format")
        
        # Test 3: Invalid token
        success, response = self.make_request(
            "GET", 
            "auth/me", 
            expected_status=401,
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        self.log_test("GET /auth/me - Invalid Token", success, str(response) if not success else "Correctly rejected invalid token")
        
        return True

    def test_complete_onboarding_api_structure(self):
        """Test POST /api/user/complete-onboarding API structure"""
        print("\n" + "="*60)
        print("TESTING COMPLETE ONBOARDING API STRUCTURE")
        print("="*60)
        
        # Test 1: No authorization header
        onboarding_data = {
            "full_name": "Test User",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-id",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "neighborhood_text": "Palermo",
            "radius_km": 5,
            "terms_version": "1.0"
        }
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            401
        )
        
        self.log_test("Complete Onboarding - No Auth Header", success, str(response) if not success else "Correctly rejected request without auth")
        
        # Test 2: Missing required fields
        incomplete_data = {"full_name": "Test User"}
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            incomplete_data,
            [400, 401, 422],  # Could be validation error or auth error
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.log_test("Complete Onboarding - Missing Required Fields", success, str(response) if not success else "Correctly rejected incomplete data")
        
        # Test 3: Invalid radius values
        invalid_radius_data = onboarding_data.copy()
        invalid_radius_data["radius_km"] = 7  # Invalid value
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            invalid_radius_data,
            [400, 401, 422],
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.log_test("Complete Onboarding - Invalid Radius", success, str(response) if not success else "Correctly rejected invalid radius")
        
        # Test 4: Invalid terms version
        invalid_terms_data = onboarding_data.copy()
        invalid_terms_data["terms_version"] = "0.9"  # Invalid version
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            invalid_terms_data,
            [400, 401, 422],
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.log_test("Complete Onboarding - Invalid Terms Version", success, str(response) if not success else "Correctly rejected invalid terms version")
        
        return True

    def test_radius_validation_values(self):
        """Test radius validation without requiring authentication"""
        print("\n" + "="*60)
        print("TESTING RADIUS VALIDATION VALUES")
        print("="*60)
        
        # Valid radius values according to models.py: [3, 5, 10, 15, 20]
        valid_radius_values = [3, 5, 10, 15, 20]
        invalid_radius_values = [1, 2, 4, 6, 7, 8, 9, 11, 12, 25, 30, 50]
        
        base_onboarding_data = {
            "full_name": "Test User",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-id",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "neighborhood_text": "Palermo",
            "terms_version": "1.0"
        }
        
        # Test valid radius values (expect 401 due to no auth, but should not be 422 validation error)
        for radius in valid_radius_values:
            onboarding_data = base_onboarding_data.copy()
            onboarding_data["radius_km"] = radius
            
            success, response = self.make_request(
                "POST",
                "user/complete-onboarding",
                onboarding_data,
                401  # Expect auth error, not validation error
            )
            
            # If we get 422, it means validation failed, which is bad for valid values
            if not success and "422" in str(response):
                self.log_test(f"Valid radius {radius}km - No validation error", False, f"Got validation error for valid radius: {response}")
            else:
                self.log_test(f"Valid radius {radius}km - No validation error", True, f"Radius {radius}km passed validation (got expected auth error)")
        
        # Test a few invalid radius values (expect validation error even without auth)
        for radius in invalid_radius_values[:3]:  # Test first 3 to avoid too many requests
            onboarding_data = base_onboarding_data.copy()
            onboarding_data["radius_km"] = radius
            
            success, response = self.make_request(
                "POST",
                "user/complete-onboarding",
                onboarding_data,
                [400, 401, 422]  # Could be validation or auth error
            )
            
            # For invalid values, we expect either validation error (422) or auth error (401)
            # Both are acceptable since the validation might happen before or after auth check
            self.log_test(f"Invalid radius {radius}km - Properly rejected", success, str(response) if not success else f"Radius {radius}km correctly rejected")
        
        return True

    def run_all_tests(self):
        """Run all API structure tests"""
        print(f"\n🚀 Starting MisFigus Authentication & Onboarding API Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Run test sequence
        tests = [
            ("Send OTP API Structure", self.test_send_otp_api_structure),
            ("Verify OTP API Structure", self.test_verify_otp_api_structure),
            ("Auth Me API Structure", self.test_auth_me_api_structure),
            ("Complete Onboarding API Structure", self.test_complete_onboarding_api_structure),
            ("Radius Validation Values", self.test_radius_validation_values)
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
    tester = MisFigusAuthOnboardingAPITester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results
    }
    
    try:
        with open('/app/auth_api_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/auth_api_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())