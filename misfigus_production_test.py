import requests
import sys
import json
from datetime import datetime

class MisFigusProductionTester:
    def __init__(self):
        # Use the production URL from frontend/.env
        self.base_url = "https://translate-profile.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data from review request
        self.test_email = "verifytest@gmail.com"
        self.qatar_album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"

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
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 {method} {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)

            print(f"   Status: {response.status_code}")
            
            if response.status_code != expected_status:
                try:
                    error_data = response.json()
                    print(f"   Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error Text: {response.text[:500]}")
                return None, response.status_code
            
            try:
                return response.json(), response.status_code
            except:
                return {}, response.status_code

        except Exception as e:
            print(f"   Exception: {str(e)}")
            return None, 0

    def test_login_flow(self):
        """Test login and get token for verifytest@gmail.com"""
        print("\n" + "="*60)
        print("TESTING LOGIN FLOW FOR verifytest@gmail.com")
        print("="*60)
        
        # Step 1: Send OTP
        print(f"\n📧 Sending OTP to {self.test_email}...")
        otp_response, status = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": self.test_email}
        )
        
        if status != 200:
            self.log_test("Send OTP", False, f"Status {status}, Response: {otp_response}")
            return False
        
        # Check DEV_OTP_MODE functionality
        has_dev_otp = 'dev_otp' in otp_response if otp_response else False
        self.log_test(
            "DEV_OTP_MODE - dev_otp field present", 
            has_dev_otp, 
            f"Response: {otp_response}"
        )
        
        if not has_dev_otp:
            print("❌ Cannot continue without dev_otp - DEV_OTP_MODE might be disabled")
            return False
        
        dev_otp = otp_response['dev_otp']
        print(f"✅ Got dev_otp: {dev_otp}")
        
        # Step 2: Verify OTP
        print(f"\n🔐 Verifying OTP {dev_otp}...")
        verify_response, status = self.make_request(
            "POST",
            "auth/verify-otp",
            {"email": self.test_email, "otp": dev_otp}
        )
        
        if status != 200:
            self.log_test("Verify OTP", False, f"Status {status}, Response: {verify_response}")
            return False
        
        if verify_response and 'token' in verify_response:
            self.token = verify_response['token']
            self.user_id = verify_response['user']['id']
            self.log_test("Login Flow", True, f"Got token and user_id: {self.user_id}")
            print(f"✅ Logged in successfully as {self.test_email}")
            return True
        else:
            self.log_test("Login Flow", False, "No token in response")
            return False

    def test_albums_list_member_count(self):
        """Test albums list and check Qatar 2022 member count"""
        print("\n" + "="*60)
        print("TESTING ALBUMS LIST MEMBER COUNT")
        print("="*60)
        
        if not self.token:
            self.log_test("Albums List", False, "No authentication token")
            return None
        
        # Get albums list
        albums_response, status = self.make_request("GET", "albums")
        
        if status != 200:
            self.log_test("Get Albums List", False, f"Status {status}")
            return None
        
        if not albums_response:
            self.log_test("Get Albums List", False, "Empty response")
            return None
        
        # Find Qatar 2022 album
        qatar_album = None
        for album in albums_response:
            if album.get('id') == self.qatar_album_id:
                qatar_album = album
                break
        
        if not qatar_album:
            self.log_test("Find Qatar 2022 Album", False, f"Album {self.qatar_album_id} not found in list")
            return None
        
        # Check member count
        member_count = qatar_album.get('member_count')
        self.log_test(
            "Albums List - Qatar 2022 found", 
            True, 
            f"member_count: {member_count}, is_member: {qatar_album.get('is_member')}"
        )
        
        print(f"📊 Qatar 2022 Album in list:")
        print(f"   - ID: {qatar_album.get('id')}")
        print(f"   - Name: {qatar_album.get('name')}")
        print(f"   - Member Count: {member_count}")
        print(f"   - Is Member: {qatar_album.get('is_member')}")
        print(f"   - User State: {qatar_album.get('user_state')}")
        
        return member_count

    def test_album_details_member_count(self):
        """Test album details and check member count consistency"""
        print("\n" + "="*60)
        print("TESTING ALBUM DETAILS MEMBER COUNT")
        print("="*60)
        
        if not self.token:
            self.log_test("Album Details", False, "No authentication token")
            return None, None
        
        # Get album details
        album_response, status = self.make_request("GET", f"albums/{self.qatar_album_id}")
        
        if status != 200:
            self.log_test("Get Album Details", False, f"Status {status}")
            return None, None
        
        if not album_response:
            self.log_test("Get Album Details", False, "Empty response")
            return None, None
        
        member_count = album_response.get('member_count')
        members_array = album_response.get('members', [])
        
        self.log_test(
            "Album Details - Qatar 2022 retrieved", 
            True, 
            f"member_count: {member_count}, members array length: {len(members_array)}"
        )
        
        print(f"📊 Qatar 2022 Album details:")
        print(f"   - ID: {album_response.get('id')}")
        print(f"   - Name: {album_response.get('name')}")
        print(f"   - Member Count: {member_count}")
        print(f"   - Members Array Length: {len(members_array)}")
        
        # Check if current user is in members array (should NOT be)
        current_user_in_members = any(
            member.get('email') == self.test_email for member in members_array
        )
        
        self.log_test(
            "Current user NOT in members array", 
            not current_user_in_members, 
            f"Current user ({self.test_email}) found in members: {current_user_in_members}"
        )
        
        # Check for test users (@example.com emails)
        test_users = [
            member for member in members_array 
            if member.get('email', '').endswith('@example.com')
        ]
        
        self.log_test(
            "No test users (@example.com) in members", 
            len(test_users) == 0, 
            f"Found {len(test_users)} test users: {[u.get('email') for u in test_users]}"
        )
        
        print(f"\n👥 Members in album:")
        for i, member in enumerate(members_array, 1):
            print(f"   {i}. {member.get('email')} - {member.get('full_name')}")
        
        return member_count, len(members_array)

    def test_member_count_consistency(self, list_count, details_count, details_array_length):
        """Test that member counts are consistent"""
        print("\n" + "="*60)
        print("TESTING MEMBER COUNT CONSISTENCY")
        print("="*60)
        
        if list_count is None or details_count is None:
            self.log_test("Member Count Consistency", False, "Missing count data")
            return False
        
        # Test 1: Albums list count == Album details count
        counts_match = list_count == details_count
        self.log_test(
            "Albums list count == Album details count", 
            counts_match, 
            f"List: {list_count}, Details: {details_count}"
        )
        
        # Test 2: Album details count == Members array length
        array_length_match = details_count == details_array_length
        self.log_test(
            "Album details count == Members array length", 
            array_length_match, 
            f"Count: {details_count}, Array length: {details_array_length}"
        )
        
        # Overall consistency
        overall_consistent = counts_match and array_length_match
        self.log_test(
            "Overall member count consistency", 
            overall_consistent, 
            f"All counts consistent: {overall_consistent}"
        )
        
        print(f"\n📊 Member Count Summary:")
        print(f"   - Albums list member_count: {list_count}")
        print(f"   - Album details member_count: {details_count}")
        print(f"   - Members array length: {details_array_length}")
        print(f"   - All consistent: {overall_consistent}")
        
        return overall_consistent

    def test_activate_qatar_album(self):
        """Activate Qatar 2022 album if not already active"""
        print("\n" + "="*60)
        print("ENSURING QATAR 2022 ALBUM IS ACTIVATED")
        print("="*60)
        
        if not self.token:
            self.log_test("Activate Album", False, "No authentication token")
            return False
        
        # Try to activate the album
        activate_response, status = self.make_request(
            "POST", 
            f"albums/{self.qatar_album_id}/activate"
        )
        
        if status == 200:
            self.log_test("Activate Qatar 2022", True, "Album activated successfully")
            return True
        elif status == 400 and activate_response and "already activated" in str(activate_response):
            self.log_test("Activate Qatar 2022", True, "Album already activated")
            return True
        else:
            self.log_test("Activate Qatar 2022", False, f"Status {status}, Response: {activate_response}")
            return False

    def run_production_tests(self):
        """Run all production-specific tests"""
        print(f"\n🚀 Starting MisFigus Production Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test Email: {self.test_email}")
        print(f"Qatar Album ID: {self.qatar_album_id}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=10)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            self.log_test("Base URL Connectivity", False, str(e))
            return False
        
        # Step 1: Login and get token
        if not self.test_login_flow():
            print("❌ Cannot continue without authentication")
            return False
        
        # Step 2: Activate Qatar album (if needed)
        self.test_activate_qatar_album()
        
        # Step 3: Test albums list member count
        list_member_count = self.test_albums_list_member_count()
        
        # Step 4: Test album details member count
        details_member_count, members_array_length = self.test_album_details_member_count()
        
        # Step 5: Test consistency
        self.test_member_count_consistency(list_member_count, details_member_count, members_array_length)
        
        # Print final summary
        print(f"\n📊 Final Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = MisFigusProductionTester()
    success = tester.run_production_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'MisFigus Production Member Count Consistency',
        'base_url': tester.base_url,
        'test_email': tester.test_email,
        'qatar_album_id': tester.qatar_album_id,
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'overall_success': success,
        'results': tester.test_results
    }
    
    # Create test_reports directory if it doesn't exist
    import os
    os.makedirs('/app/test_reports', exist_ok=True)
    
    with open('/app/test_reports/misfigus_production_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to /app/test_reports/misfigus_production_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())