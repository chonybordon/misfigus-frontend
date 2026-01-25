import requests
import sys
import json
import time
from datetime import datetime

class MisFigusAuthOnboardingComprehensiveTester:
    def __init__(self, base_url="https://translate-profile.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_email = None

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

    def create_test_user(self, email_suffix=""):
        """Create a test user and return token"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        test_email = f"misfigus.test.{timestamp}{email_suffix}@gmail.com"
        
        # Send OTP
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": test_email},
            200
        )
        
        if not success:
            return None, None, test_email
        
        # Wait a bit to avoid rate limits
        time.sleep(1)
        
        # Get OTP from logs
        otp_code = self.extract_otp_from_logs()
        if not otp_code:
            return None, None, test_email
        
        # Verify OTP
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": test_email, "otp": otp_code},
            200
        )
        
        if success and 'token' in response:
            return response['token'], response['user']['id'], test_email
        
        return None, None, test_email

    def test_radius_validation_comprehensive(self):
        """Test radius validation with all valid and invalid values"""
        print("\n" + "="*60)
        print("TESTING RADIUS VALIDATION COMPREHENSIVE")
        print("="*60)
        
        # Valid radius values according to models.py
        valid_radius_values = [3, 5, 10, 15, 20]
        invalid_radius_values = [1, 2, 4, 6, 7, 8, 9, 11, 12, 25, 30, 50]
        
        base_onboarding_data = {
            "full_name": "Test User Radius",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-id-radius",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "neighborhood_text": "Palermo",
            "terms_version": "1.0"
        }
        
        # Test valid radius values
        for radius in valid_radius_values:
            token, user_id, email = self.create_test_user(f".radius.{radius}")
            if not token:
                self.log_test(f"Create user for radius {radius}km test", False, "Failed to create test user")
                continue
            
            # Set token temporarily
            old_token = self.token
            self.token = token
            
            onboarding_data = base_onboarding_data.copy()
            onboarding_data["radius_km"] = radius
            
            success, response = self.make_request(
                "POST",
                "user/complete-onboarding",
                onboarding_data,
                200
            )
            
            self.log_test(
                f"Valid radius {radius}km accepted", 
                success, 
                str(response) if not success else f"Radius {radius}km correctly accepted"
            )
            
            # Restore token
            self.token = old_token
            
            # Add delay to avoid rate limits
            time.sleep(0.5)
        
        # Test invalid radius values
        for radius in invalid_radius_values[:5]:  # Test first 5 to avoid too many requests
            token, user_id, email = self.create_test_user(f".invalid.{radius}")
            if not token:
                self.log_test(f"Create user for invalid radius {radius}km test", False, "Failed to create test user")
                continue
            
            # Set token temporarily
            old_token = self.token
            self.token = token
            
            onboarding_data = base_onboarding_data.copy()
            onboarding_data["radius_km"] = radius
            
            success, response = self.make_request(
                "POST",
                "user/complete-onboarding",
                onboarding_data,
                400
            )
            
            self.log_test(
                f"Invalid radius {radius}km rejected", 
                success, 
                str(response) if not success else f"Radius {radius}km correctly rejected"
            )
            
            # Restore token
            self.token = old_token
            
            # Add delay to avoid rate limits
            time.sleep(0.5)
        
        return True

    def test_onboarding_flow_complete(self):
        """Test complete onboarding flow from start to finish"""
        print("\n" + "="*60)
        print("TESTING COMPLETE ONBOARDING FLOW")
        print("="*60)
        
        # Step 1: Send OTP
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.test_email = f"misfigus.complete.flow.{timestamp}@gmail.com"
        
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": self.test_email},
            200
        )
        
        self.log_test("Step 1: Send OTP", success, str(response) if not success else "")
        
        if not success:
            return False
        
        # Step 2: Verify OTP
        time.sleep(1)  # Wait for OTP
        otp_code = self.extract_otp_from_logs()
        
        if not otp_code:
            self.log_test("Step 2: Extract OTP", False, "Could not find OTP in logs")
            return False
        
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": self.test_email, "otp": otp_code},
            200
        )
        
        self.log_test("Step 2: Verify OTP", success, str(response) if not success else "")
        
        if not success or 'token' not in response:
            return False
        
        self.token = response['token']
        self.user_id = response['user']['id']
        
        # Verify user has onboarding_completed = false
        onboarding_incomplete = response['user'].get('onboarding_completed') == False
        self.log_test("Step 2: User onboarding incomplete initially", onboarding_incomplete, 
                     f"onboarding_completed = {response['user'].get('onboarding_completed')}")
        
        # Step 3: Check /auth/me before onboarding
        success, me_response = self.make_request("GET", "auth/me", expected_status=200)
        
        self.log_test("Step 3: GET /auth/me before onboarding", success, str(me_response) if not success else "")
        
        if success:
            me_onboarding_incomplete = me_response.get('onboarding_completed') == False
            self.log_test("Step 3: /auth/me shows onboarding incomplete", me_onboarding_incomplete,
                         f"onboarding_completed = {me_response.get('onboarding_completed')}")
        
        # Step 4: Complete onboarding
        onboarding_data = {
            "full_name": "Complete Flow Test User",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-complete-flow",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "neighborhood_text": "Palermo",
            "radius_km": 10,
            "terms_version": "1.0"
        }
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            200
        )
        
        self.log_test("Step 4: Complete onboarding", success, str(response) if not success else "")
        
        if success:
            # Verify all fields are set correctly
            user = response.get('user', {})
            
            checks = [
                ("onboarding_completed = true", user.get('onboarding_completed') == True),
                ("full_name set", user.get('full_name') == onboarding_data['full_name']),
                ("display_name set", user.get('display_name') == onboarding_data['full_name']),
                ("country_code set", user.get('country_code') == onboarding_data['country_code']),
                ("city_name set", user.get('city_name') == onboarding_data['city_name']),
                ("radius_km set", user.get('radius_km') == onboarding_data['radius_km']),
                ("terms_accepted = true", user.get('terms_accepted') == True),
                ("terms_version set", user.get('terms_version') == onboarding_data['terms_version']),
            ]
            
            for check_name, check_result in checks:
                self.log_test(f"Step 4: {check_name}", check_result, f"Expected vs actual mismatch")
        
        # Step 5: Check /auth/me after onboarding
        success, me_response = self.make_request("GET", "auth/me", expected_status=200)
        
        self.log_test("Step 5: GET /auth/me after onboarding", success, str(me_response) if not success else "")
        
        if success:
            me_onboarding_complete = me_response.get('onboarding_completed') == True
            self.log_test("Step 5: /auth/me shows onboarding complete", me_onboarding_complete,
                         f"onboarding_completed = {me_response.get('onboarding_completed')}")
        
        # Step 6: Try to complete onboarding again (should fail)
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            400
        )
        
        self.log_test("Step 6: Re-onboarding blocked", success, str(response) if not success else "Correctly blocked re-onboarding")
        
        return True

    def test_terms_version_validation(self):
        """Test terms version validation"""
        print("\n" + "="*60)
        print("TESTING TERMS VERSION VALIDATION")
        print("="*60)
        
        # Create test user
        token, user_id, email = self.create_test_user(".terms")
        if not token:
            self.log_test("Create user for terms test", False, "Failed to create test user")
            return False
        
        # Set token temporarily
        old_token = self.token
        self.token = token
        
        # Test with invalid terms version
        onboarding_data = {
            "full_name": "Terms Test User",
            "country_code": "AR",
            "region_name": "Buenos Aires",
            "city_name": "Buenos Aires",
            "place_id": "test-place-terms",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "neighborhood_text": "Palermo",
            "radius_km": 5,
            "terms_version": "0.9"  # Invalid version
        }
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            400
        )
        
        self.log_test("Invalid terms version rejected", success, str(response) if not success else "Correctly rejected invalid terms version")
        
        # Test with valid terms version
        onboarding_data["terms_version"] = "1.0"  # Valid version
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            200
        )
        
        self.log_test("Valid terms version accepted", success, str(response) if not success else "Correctly accepted valid terms version")
        
        # Restore token
        self.token = old_token
        
        return True

    def run_all_tests(self):
        """Run all comprehensive authentication and onboarding tests"""
        print(f"\n🚀 Starting MisFigus Comprehensive Authentication & Onboarding Tests")
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
            ("Complete Onboarding Flow", self.test_onboarding_flow_complete),
            ("Radius Validation Comprehensive", self.test_radius_validation_comprehensive),
            ("Terms Version Validation", self.test_terms_version_validation)
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
    tester = MisFigusAuthOnboardingComprehensiveTester()
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
        with open('/app/comprehensive_auth_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/comprehensive_auth_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())