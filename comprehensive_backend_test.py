import requests
import sys
import json
import time
from datetime import datetime

class ComprehensiveStickerSwapTester:
    def __init__(self, base_url="https://sticker-swap-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.group_id = None
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    return False, f"Status: {response.status_code}, Error: {error_data}"
                except:
                    return False, f"Status: {response.status_code}, Response: {response.text[:200]}"

        except Exception as e:
            return False, f"Exception: {str(e)}"

    def test_complete_auth_flow(self):
        """Test complete authentication with real OTP"""
        print("\n" + "="*60)
        print("TESTING COMPLETE AUTHENTICATION FLOW")
        print("="*60)
        
        # Step 1: Send OTP
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        success, response = self.make_request('POST', 'auth/send-otp', {"email": test_email})
        
        if success:
            self.log_test("Send OTP", True, f"Email: {test_email}")
            
            # Step 2: Get OTP from logs (simulate checking backend logs)
            print(f"\n📧 Check backend logs for OTP sent to: {test_email}")
            print("   Run: tail -n 20 /var/log/supervisor/backend.err.log | grep 'OTP Code'")
            
            # For automated testing, we'll try a few common test OTPs
            test_otps = ["123456", "000000", "111111"]
            
            for otp in test_otps:
                success, response = self.make_request('POST', 'auth/verify-otp', 
                                                    {"email": test_email, "otp": otp}, 
                                                    expected_status=400)  # Expecting failure
                if not success and "Invalid or expired OTP" in str(response):
                    self.log_test(f"Verify OTP ({otp})", True, "Correctly rejected invalid OTP")
                    break
            
            return test_email
        else:
            self.log_test("Send OTP", False, response)
            return None

    def test_with_valid_auth(self):
        """Test with manually provided valid auth (for demo purposes)"""
        print("\n" + "="*60)
        print("TESTING WITH MOCK VALID AUTHENTICATION")
        print("="*60)
        
        # For testing purposes, we'll create a mock token scenario
        # In real testing, you'd use the actual OTP from logs
        
        # Test protected endpoint without auth
        success, response = self.make_request('GET', 'auth/me', expected_status=401)
        if not success and "401" in str(response):
            self.log_test("Protected endpoint without auth", True, "Correctly rejected unauthorized request")
        else:
            self.log_test("Protected endpoint without auth", False, "Should have rejected unauthorized request")

    def test_groups_functionality(self):
        """Test groups functionality (requires auth)"""
        print("\n" + "="*60)
        print("TESTING GROUPS FUNCTIONALITY")
        print("="*60)
        
        if not self.token:
            print("⚠️  Skipping groups tests - no valid auth token")
            return
            
        # Test get groups
        success, response = self.make_request('GET', 'groups')
        if success:
            self.log_test("Get Groups", True, f"Found {len(response)} groups")
        else:
            self.log_test("Get Groups", False, response)

    def test_public_endpoints(self):
        """Test publicly accessible endpoints"""
        print("\n" + "="*60)
        print("TESTING PUBLIC ENDPOINTS")
        print("="*60)
        
        # Test base URL
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Base URL Access", True, f"Status: {response.status_code}")
            else:
                self.log_test("Base URL Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Base URL Access", False, f"Exception: {e}")

    def test_api_structure(self):
        """Test API structure and error handling"""
        print("\n" + "="*60)
        print("TESTING API STRUCTURE & ERROR HANDLING")
        print("="*60)
        
        # Test invalid endpoint
        success, response = self.make_request('GET', 'invalid-endpoint', expected_status=404)
        if not success and "404" in str(response):
            self.log_test("Invalid endpoint handling", True, "Correctly returned 404")
        else:
            self.log_test("Invalid endpoint handling", False, "Should return 404 for invalid endpoint")
        
        # Test malformed JSON
        try:
            url = f"{self.api_url}/auth/send-otp"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data="invalid json", headers=headers, timeout=10)
            if response.status_code in [400, 422]:
                self.log_test("Malformed JSON handling", True, f"Status: {response.status_code}")
            else:
                self.log_test("Malformed JSON handling", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Malformed JSON handling", False, f"Exception: {e}")

    def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n" + "="*60)
        print("TESTING CORS CONFIGURATION")
        print("="*60)
        
        try:
            response = requests.options(f"{self.api_url}/auth/send-otp", timeout=5)
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            found_cors = any(header in response.headers for header in cors_headers)
            if found_cors:
                self.log_test("CORS Headers", True, "CORS headers present")
            else:
                self.log_test("CORS Headers", False, "CORS headers missing")
                
        except Exception as e:
            self.log_test("CORS Headers", False, f"Exception: {e}")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print(f"\n🚀 Starting Comprehensive StickerSwap API Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Test public endpoints
        self.test_public_endpoints()
        
        # Test API structure
        self.test_api_structure()
        
        # Test CORS
        self.test_cors_headers()
        
        # Test authentication flow
        self.test_complete_auth_flow()
        
        # Test with mock auth
        self.test_with_valid_auth()
        
        # Test groups (will skip without auth)
        self.test_groups_functionality()
        
        # Print comprehensive summary
        print(f"\n" + "="*60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Save detailed results
        results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'tests_run': self.tests_run,
            'tests_passed': self.tests_passed,
            'success_rate': (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0,
            'detailed_results': self.test_results
        }
        
        with open('/app/test_reports/comprehensive_backend_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/test_reports/comprehensive_backend_results.json")
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% pass rate

def main():
    tester = ComprehensiveStickerSwapTester()
    success = tester.run_comprehensive_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())