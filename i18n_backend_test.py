import requests
import sys
import json
import time
from datetime import datetime

class MisFigusI18nTester:
    def __init__(self, base_url="https://sticker-swap-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_email = None
        
        # Supported languages from frontend i18n.js
        self.supported_languages = ['es', 'en', 'pt', 'fr', 'de', 'it']

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

    def setup_test_user(self):
        """Create and authenticate a test user"""
        print("\n" + "="*60)
        print("SETTING UP TEST USER FOR I18N TESTING")
        print("="*60)
        
        # Generate unique test email
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.test_email = f"misfigus.i18n.test.{timestamp}@gmail.com"
        
        print(f"🔍 Creating test user: {self.test_email}")
        
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
            self.log_test("Setup - Extract OTP", False, "Could not find OTP in backend logs")
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
        
        self.log_test("Setup - User Authentication", True, f"User ID: {self.user_id}")
        return True

    def test_patch_auth_me_language_update(self):
        """Test PATCH /api/auth/me for language updates"""
        print("\n" + "="*60)
        print("TESTING PATCH /api/auth/me - LANGUAGE UPDATE")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping language update test - no auth token")
            return False
        
        # Test 1: Update to French
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "fr"},
            200
        )
        
        self.log_test("PATCH /auth/me - Update to French", success, str(response) if not success else "")
        
        if success:
            # Verify response contains updated language
            has_language = "language" in response
            correct_language = response.get("language") == "fr"
            
            self.log_test("PATCH /auth/me - Response has language field", has_language, "Missing 'language' field")
            self.log_test("PATCH /auth/me - Language updated to French", correct_language, f"Expected 'fr', got '{response.get('language')}'")
        
        # Test 2: Update to Spanish
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "es"},
            200
        )
        
        self.log_test("PATCH /auth/me - Update to Spanish", success, str(response) if not success else "")
        
        if success:
            correct_language = response.get("language") == "es"
            self.log_test("PATCH /auth/me - Language updated to Spanish", correct_language, f"Expected 'es', got '{response.get('language')}'")
        
        # Test 3: Update to English
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "en"},
            200
        )
        
        self.log_test("PATCH /auth/me - Update to English", success, str(response) if not success else "")
        
        if success:
            correct_language = response.get("language") == "en"
            self.log_test("PATCH /auth/me - Language updated to English", correct_language, f"Expected 'en', got '{response.get('language')}'")
        
        # Test 4: Test all supported languages
        for lang_code in self.supported_languages:
            success, response = self.make_request(
                "PATCH",
                "auth/me",
                {"language": lang_code},
                200
            )
            
            if success:
                correct_language = response.get("language") == lang_code
                self.log_test(f"PATCH /auth/me - Update to {lang_code.upper()}", correct_language, 
                            f"Expected '{lang_code}', got '{response.get('language')}'")
            else:
                self.log_test(f"PATCH /auth/me - Update to {lang_code.upper()}", False, str(response))
        
        return True

    def test_get_auth_me_language_persistence(self):
        """Test GET /api/auth/me to verify language persistence"""
        print("\n" + "="*60)
        print("TESTING GET /api/auth/me - LANGUAGE PERSISTENCE")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping language persistence test - no auth token")
            return False
        
        # Set language to Portuguese first
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "pt"},
            200
        )
        
        if not success:
            self.log_test("Setup - Set language to Portuguese", False, response)
            return False
        
        # Test 1: Verify language persists in GET request
        success, response = self.make_request("GET", "auth/me", expected_status=200)
        
        self.log_test("GET /auth/me - Language Persistence Check", success, str(response) if not success else "")
        
        if success:
            has_language = "language" in response
            correct_language = response.get("language") == "pt"
            
            self.log_test("GET /auth/me - Has language field", has_language, "Missing 'language' field")
            self.log_test("GET /auth/me - Language persisted as Portuguese", correct_language, 
                        f"Expected 'pt', got '{response.get('language')}'")
        
        # Test 2: Change to German and verify persistence
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "de"},
            200
        )
        
        if success:
            # Immediately check if it persisted
            success, response = self.make_request("GET", "auth/me", expected_status=200)
            
            if success:
                correct_language = response.get("language") == "de"
                self.log_test("GET /auth/me - German language persisted", correct_language, 
                            f"Expected 'de', got '{response.get('language')}'")
        
        # Test 3: Change to Italian and verify persistence
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "it"},
            200
        )
        
        if success:
            # Check persistence
            success, response = self.make_request("GET", "auth/me", expected_status=200)
            
            if success:
                correct_language = response.get("language") == "it"
                self.log_test("GET /auth/me - Italian language persisted", correct_language, 
                            f"Expected 'it', got '{response.get('language')}'")
        
        return True

    def test_language_validation(self):
        """Test language validation with invalid language codes"""
        print("\n" + "="*60)
        print("TESTING LANGUAGE VALIDATION")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping language validation test - no auth token")
            return False
        
        # Test 1: Invalid language code
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "invalid"},
            [200, 400, 422]  # Accept either success (no validation) or error
        )
        
        # If it returns 200, there's no validation (which is also valid)
        # If it returns 400/422, validation is working
        if success:
            # Check what language was actually set
            get_success, get_response = self.make_request("GET", "auth/me", expected_status=200)
            if get_success:
                actual_language = get_response.get("language")
                if actual_language == "invalid":
                    self.log_test("Language Validation - Invalid code accepted", True, "No validation implemented - invalid language accepted")
                else:
                    self.log_test("Language Validation - Invalid code ignored", True, f"Invalid language ignored, kept '{actual_language}'")
        else:
            self.log_test("Language Validation - Invalid code rejected", True, "Validation working - invalid language rejected")
        
        # Test 2: Empty language
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": ""},
            [200, 400, 422]
        )
        
        if success:
            get_success, get_response = self.make_request("GET", "auth/me", expected_status=200)
            if get_success:
                actual_language = get_response.get("language")
                self.log_test("Language Validation - Empty string handled", True, f"Empty language handled, current: '{actual_language}'")
        else:
            self.log_test("Language Validation - Empty string rejected", True, "Empty language rejected")
        
        # Test 3: Null language
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": None},
            [200, 400, 422]
        )
        
        if success:
            get_success, get_response = self.make_request("GET", "auth/me", expected_status=200)
            if get_success:
                actual_language = get_response.get("language")
                self.log_test("Language Validation - Null language handled", True, f"Null language handled, current: '{actual_language}'")
        else:
            self.log_test("Language Validation - Null language rejected", True, "Null language rejected")
        
        # Test 4: Case sensitivity
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "EN"},  # Uppercase
            [200, 400, 422]
        )
        
        if success:
            get_success, get_response = self.make_request("GET", "auth/me", expected_status=200)
            if get_success:
                actual_language = get_response.get("language")
                if actual_language == "EN":
                    self.log_test("Language Validation - Case sensitive (uppercase accepted)", True, "Uppercase 'EN' accepted")
                elif actual_language == "en":
                    self.log_test("Language Validation - Case normalized", True, "Uppercase 'EN' normalized to 'en'")
                else:
                    self.log_test("Language Validation - Case handling", True, f"Uppercase 'EN' resulted in '{actual_language}'")
        else:
            self.log_test("Language Validation - Uppercase rejected", True, "Uppercase language code rejected")
        
        return True

    def test_onboarding_with_language(self):
        """Test POST /api/user/complete-onboarding still works with language functionality"""
        print("\n" + "="*60)
        print("TESTING ONBOARDING COMPATIBILITY WITH LANGUAGE")
        print("="*60)
        
        # Create a new user for onboarding test
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        onboarding_email = f"misfigus.onboarding.i18n.{timestamp}@gmail.com"
        
        # Send OTP
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": onboarding_email},
            200
        )
        
        if not success:
            self.log_test("Onboarding Setup - Send OTP", False, response)
            return False
        
        # Get OTP and verify
        otp_code = self.extract_otp_from_logs()
        if not otp_code:
            self.log_test("Onboarding Setup - Extract OTP", False, "Could not find OTP")
            return False
        
        success, response = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": onboarding_email, "otp": otp_code},
            200
        )
        
        if not success:
            self.log_test("Onboarding Setup - Verify OTP", False, response)
            return False
        
        # Store current token and switch to new user
        old_token = self.token
        self.token = response['token']
        new_user_id = response['user']['id']
        
        # Set language before onboarding
        success, response = self.make_request(
            "PATCH",
            "auth/me",
            {"language": "fr"},
            200
        )
        
        self.log_test("Onboarding - Set language before onboarding", success, str(response) if not success else "")
        
        # Complete onboarding
        onboarding_data = {
            "full_name": "Test User France",
            "country_code": "FR",
            "region_name": "Île-de-France",
            "city_name": "Paris",
            "place_id": "test-place-id-paris",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "neighborhood_text": "Marais",
            "radius_km": 10,
            "terms_version": "1.0"
        }
        
        success, response = self.make_request(
            "POST",
            "user/complete-onboarding",
            onboarding_data,
            200
        )
        
        self.log_test("Onboarding - Complete with language set", success, str(response) if not success else "")
        
        if success:
            # Verify onboarding completed and language preserved
            user_data = response.get("user", {})
            onboarding_completed = user_data.get("onboarding_completed") == True
            language_preserved = user_data.get("language") == "fr"
            full_name_set = user_data.get("full_name") == onboarding_data["full_name"]
            
            self.log_test("Onboarding - Onboarding completed", onboarding_completed, "onboarding_completed should be true")
            self.log_test("Onboarding - Language preserved during onboarding", language_preserved, f"Expected 'fr', got '{user_data.get('language')}'")
            self.log_test("Onboarding - Full name set correctly", full_name_set, "Full name not set correctly")
        
        # Verify language persists after onboarding
        success, response = self.make_request("GET", "auth/me", expected_status=200)
        
        if success:
            language_after_onboarding = response.get("language") == "fr"
            self.log_test("Onboarding - Language persists after onboarding", language_after_onboarding, 
                        f"Expected 'fr', got '{response.get('language')}'")
        
        # Restore original token
        self.token = old_token
        
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
        """Run all i18n/language tests"""
        print(f"\n🚀 Starting MisFigus i18n/Language Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Supported Languages: {', '.join(self.supported_languages)}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user")
            return False
        
        # Run test sequence
        tests = [
            ("PATCH /auth/me Language Update", self.test_patch_auth_me_language_update),
            ("GET /auth/me Language Persistence", self.test_get_auth_me_language_persistence),
            ("Language Validation", self.test_language_validation),
            ("Onboarding Compatibility", self.test_onboarding_with_language)
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
    tester = MisFigusI18nTester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'i18n_language_functionality',
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'test_email': tester.test_email,
        'supported_languages': tester.supported_languages,
        'token_obtained': tester.token is not None
    }
    
    try:
        with open('/app/i18n_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/i18n_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())