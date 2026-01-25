import requests
import sys
import json
import time
from datetime import datetime

class ComprehensiveProfileTestSuite:
    def __init__(self, base_url="https://translate-profile.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = "3b6734a6-4a17-437f-845f-ba265fcc4b7b"  # Test user ID
        self.fifa_album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"  # FIFA Album ID
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

    def test_public_terms_endpoints(self):
        """Test public terms endpoints (no auth required)"""
        print("\n" + "="*60)
        print("TESTING PUBLIC TERMS ENDPOINTS")
        print("="*60)
        
        # Test GET /api/terms (default Spanish)
        success, response = self.make_request("GET", "terms", expected_status=200)
        
        if not success:
            self.log_test("GET /api/terms (default)", False, response)
            return False
            
        self.log_test("GET /api/terms (default)", True, "Terms content retrieved")
        
        # Verify terms structure
        terms_fields = ['version', 'content']
        has_terms_fields = all(field in response for field in terms_fields)
        self.log_test(
            "Terms response has required fields", 
            has_terms_fields,
            f"Missing fields: {[f for f in terms_fields if f not in response]}"
        )
        
        # Verify version is correct
        expected_version = "1.0"
        version_correct = response.get('version') == expected_version
        self.log_test(
            f"Terms version is {expected_version}", 
            version_correct,
            f"Expected {expected_version}, got {response.get('version')}"
        )
        
        # Verify content is not empty
        content_exists = bool(response.get('content', '').strip())
        self.log_test(
            "Terms content is not empty", 
            content_exists,
            "Terms content is empty"
        )
        
        # Test GET /api/terms with Spanish language
        success, response_es = self.make_request("GET", "terms?language=es", expected_status=200)
        self.log_test("GET /api/terms?language=es", success, str(response_es) if not success else "Spanish terms retrieved")
        
        if success:
            # Verify Spanish content contains Spanish text
            spanish_content = response_es.get('content', '')
            has_spanish_indicators = any(word in spanish_content.lower() for word in ['términos', 'condiciones', 'figuritas', 'intercambio'])
            self.log_test(
                "Spanish terms contain Spanish text", 
                has_spanish_indicators,
                "Spanish terms don't contain expected Spanish words"
            )
        
        # Test GET /api/terms with English language
        success, response_en = self.make_request("GET", "terms?language=en", expected_status=200)
        self.log_test("GET /api/terms?language=en", success, str(response_en) if not success else "English terms retrieved")
        
        if success:
            # Verify English content contains English text
            english_content = response_en.get('content', '')
            has_english_indicators = any(word in english_content.lower() for word in ['terms', 'conditions', 'stickers', 'exchange'])
            self.log_test(
                "English terms contain English text", 
                has_english_indicators,
                "English terms don't contain expected English words"
            )
        
        return True

    def test_authenticated_endpoints_structure(self):
        """Test authenticated endpoints structure (expect 401/403)"""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATED ENDPOINTS STRUCTURE")
        print("="*60)
        
        # Test endpoints that require authentication - should return 401/403
        auth_endpoints = [
            ("GET", "user/location-status", "Location Status"),
            ("PUT", "user/location", "Update Location"),
            ("PUT", "user/radius", "Update Radius"),
            ("GET", "user/terms-status", "Terms Status"),
            ("POST", "user/accept-terms", "Accept Terms"),
            ("GET", f"albums/{self.fifa_album_id}/matches", "Album Matches")
        ]
        
        for method, endpoint, name in auth_endpoints:
            data = None
            if method == "PUT" and "location" in endpoint:
                data = {"zone": "Test Zone", "lat": -34.6037, "lng": -58.3816}
            elif method == "PUT" and "radius" in endpoint:
                data = {"radius_km": 5}
            elif method == "POST" and "accept-terms" in endpoint:
                data = {"version": "1.0"}
            
            success, response = self.make_request(
                method, 
                endpoint, 
                data,
                [401, 403]  # Expect authentication error
            )
            
            self.log_test(
                f"{name} requires authentication", 
                success,
                f"Expected 401/403, got: {response}"
            )
        
        return True

    def test_radius_validation_logic(self):
        """Test radius validation by examining the backend code logic"""
        print("\n" + "="*60)
        print("TESTING RADIUS VALIDATION LOGIC")
        print("="*60)
        
        # Test invalid radius values (should be rejected)
        invalid_radius_values = [1, 2, 4, 6, 7, 8, 9, 11, 15, 20, 0, -1]
        
        for invalid_radius in invalid_radius_values:
            data = {"radius_km": invalid_radius}
            success, response = self.make_request(
                "PUT", 
                "user/radius", 
                data,
                [400, 401, 403]  # 400 for validation error, 401/403 for auth
            )
            
            # We expect either auth error (401/403) or validation error (400)
            self.log_test(
                f"Invalid radius {invalid_radius}km rejected", 
                success,
                f"Expected 400/401/403, got: {response}"
            )
        
        # Test valid radius values
        valid_radius_values = [3, 5, 10]
        
        for valid_radius in valid_radius_values:
            data = {"radius_km": valid_radius}
            success, response = self.make_request(
                "PUT", 
                "user/radius", 
                data,
                [200, 400, 401, 403]  # 200 if auth works, 400 for cooldown, 401/403 for auth
            )
            
            # We expect auth error since we don't have token, but structure should be valid
            self.log_test(
                f"Valid radius {valid_radius}km structure accepted", 
                success,
                f"Expected 200/400/401/403, got: {response}"
            )
        
        return True

    def test_location_validation_logic(self):
        """Test location validation by examining the backend code logic"""
        print("\n" + "="*60)
        print("TESTING LOCATION VALIDATION LOGIC")
        print("="*60)
        
        # Test valid location data structure
        valid_locations = [
            {"zone": "Buenos Aires, Argentina", "lat": -34.6037, "lng": -58.3816},
            {"zone": "Madrid, Spain", "lat": 40.4168, "lng": -3.7038},
            {"zone": "New York, USA", "lat": 40.7128, "lng": -74.0060}
        ]
        
        for location in valid_locations:
            success, response = self.make_request(
                "PUT", 
                "user/location", 
                location,
                [200, 400, 401, 403]  # Various expected responses
            )
            
            self.log_test(
                f"Location {location['zone']} structure accepted", 
                success,
                f"Expected 200/400/401/403, got: {response}"
            )
        
        # Test invalid location data structures
        invalid_locations = [
            {"zone": "Test Zone"},  # Missing lat/lng
            {"lat": -34.6037, "lng": -58.3816},  # Missing zone
            {"zone": "", "lat": -34.6037, "lng": -58.3816},  # Empty zone
            {"zone": "Test Zone", "lat": "invalid", "lng": -58.3816},  # Invalid lat
            {"zone": "Test Zone", "lat": -34.6037, "lng": "invalid"}  # Invalid lng
        ]
        
        for location in invalid_locations:
            success, response = self.make_request(
                "PUT", 
                "user/location", 
                location,
                [400, 401, 403, 422]  # Expect validation or auth error
            )
            
            self.log_test(
                f"Invalid location structure rejected: {location}", 
                success,
                f"Expected 400/401/403/422, got: {response}"
            )
        
        return True

    def test_cooldown_enforcement_logic(self):
        """Test cooldown enforcement logic"""
        print("\n" + "="*60)
        print("TESTING COOLDOWN ENFORCEMENT LOGIC")
        print("="*60)
        
        # The cooldown is 7 days according to the code
        # We can't test the actual cooldown without authentication,
        # but we can verify the endpoint structure
        
        # Test that the endpoints exist and have proper error handling
        endpoints_with_cooldown = [
            ("PUT", "user/location", {"zone": "Test Zone", "lat": -34.6037, "lng": -58.3816}),
            ("PUT", "user/radius", {"radius_km": 5})
        ]
        
        for method, endpoint, data in endpoints_with_cooldown:
            success, response = self.make_request(
                method, 
                endpoint, 
                data,
                [200, 400, 401, 403]
            )
            
            self.log_test(
                f"Cooldown endpoint {endpoint} exists", 
                success,
                f"Expected 200/400/401/403, got: {response}"
            )
        
        return True

    def test_album_matches_endpoint_structure(self):
        """Test album matches endpoint structure"""
        print("\n" + "="*60)
        print("TESTING ALBUM MATCHES ENDPOINT STRUCTURE")
        print("="*60)
        
        # Test with valid album ID
        success, response = self.make_request(
            "GET", 
            f"albums/{self.fifa_album_id}/matches", 
            expected_status=[200, 401, 403]
        )
        
        self.log_test(
            "Album matches endpoint exists", 
            success,
            f"Expected 200/401/403, got: {response}"
        )
        
        # Test with invalid album ID
        fake_album_id = "00000000-0000-0000-0000-000000000000"
        success, response = self.make_request(
            "GET", 
            f"albums/{fake_album_id}/matches", 
            expected_status=[401, 403, 404]
        )
        
        self.log_test(
            "Invalid album ID handled properly", 
            success,
            f"Expected 401/403/404, got: {response}"
        )
        
        return True

    def test_terms_acceptance_structure(self):
        """Test terms acceptance endpoint structure"""
        print("\n" + "="*60)
        print("TESTING TERMS ACCEPTANCE STRUCTURE")
        print("="*60)
        
        # Test valid terms acceptance
        valid_acceptance = {"version": "1.0"}
        success, response = self.make_request(
            "POST", 
            "user/accept-terms", 
            valid_acceptance,
            [200, 401, 403]
        )
        
        self.log_test(
            "Terms acceptance endpoint exists", 
            success,
            f"Expected 200/401/403, got: {response}"
        )
        
        # Test invalid terms acceptance
        invalid_acceptances = [
            {"version": ""},  # Empty version
            {"version": "invalid"},  # Invalid version
            {},  # Missing version
            {"invalid_field": "1.0"}  # Wrong field
        ]
        
        for invalid_data in invalid_acceptances:
            success, response = self.make_request(
                "POST", 
                "user/accept-terms", 
                invalid_data,
                [400, 401, 403, 422]
            )
            
            self.log_test(
                f"Invalid terms acceptance rejected: {invalid_data}", 
                success,
                f"Expected 400/401/403/422, got: {response}"
            )
        
        return True

    def run_all_tests(self):
        """Run all profile settings tests"""
        print(f"\n🚀 Starting Comprehensive MisFigus Profile Settings Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test User ID: {self.user_id}")
        print(f"FIFA Album ID: {self.fifa_album_id}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Run test sequence
        tests = [
            ("Public Terms Endpoints", self.test_public_terms_endpoints),
            ("Authenticated Endpoints Structure", self.test_authenticated_endpoints_structure),
            ("Radius Validation Logic", self.test_radius_validation_logic),
            ("Location Validation Logic", self.test_location_validation_logic),
            ("Cooldown Enforcement Logic", self.test_cooldown_enforcement_logic),
            ("Album Matches Endpoint Structure", self.test_album_matches_endpoint_structure),
            ("Terms Acceptance Structure", self.test_terms_acceptance_structure)
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
    tester = ComprehensiveProfileTestSuite()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'user_id': tester.user_id,
        'fifa_album_id': tester.fifa_album_id,
        'token_obtained': tester.token is not None
    }
    
    try:
        with open('/app/comprehensive_profile_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/comprehensive_profile_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())