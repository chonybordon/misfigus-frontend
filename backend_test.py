import requests
import sys
import json
import time
from datetime import datetime

class MisFigusAlbumTester:
    def __init__(self, base_url="https://groupfigu.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
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
        test_email = f"misfigus.test.{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com"
        
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

    def test_albums_endpoint(self):
        """Test GET /api/albums with user_state logic"""
        print("\n" + "="*60)
        print("TESTING ALBUMS ENDPOINT")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping albums test - no auth token")
            return False
            
        success, response = self.make_request("GET", "albums", expected_status=200)
        
        if not success:
            self.log_test("GET /api/albums", False, response)
            return False
            
        self.log_test("GET /api/albums", True, f"Retrieved {len(response)} albums")
        
        # Verify album structure and user_state logic
        albums_found = {
            'qatar_2022': None,
            'fifa_2026': None,
            'other_albums': []
        }
        
        for album in response:
            if 'Qatar' in album.get('name', '') and '2022' in album.get('name', ''):
                albums_found['qatar_2022'] = album
            elif 'FIFA' in album.get('name', '') and '2026' in album.get('name', ''):
                albums_found['fifa_2026'] = album
            else:
                albums_found['other_albums'].append(album)
        
        # Test 1: All albums should have user_state field
        all_have_user_state = all('user_state' in album for album in response)
        self.log_test(
            "All albums have user_state field", 
            all_have_user_state,
            "Some albums missing user_state field" if not all_have_user_state else ""
        )
        
        # Test 2: New user should see all available albums as INACTIVE except FIFA 2026
        inactive_count = sum(1 for album in response if album.get('user_state') == 'inactive')
        coming_soon_count = sum(1 for album in response if album.get('user_state') == 'coming_soon')
        
        self.log_test(
            "New user sees albums as INACTIVE", 
            inactive_count > 0,
            f"Found {inactive_count} inactive albums"
        )
        
        # Test 3: FIFA 2026 should be coming_soon
        if albums_found['fifa_2026']:
            fifa_state = albums_found['fifa_2026'].get('user_state')
            self.log_test(
                "FIFA 2026 is coming_soon", 
                fifa_state == 'coming_soon',
                f"FIFA 2026 state: {fifa_state}"
            )
        else:
            self.log_test("FIFA 2026 album found", False, "FIFA 2026 album not found")
        
        # Test 4: Qatar 2022 should be inactive initially
        if albums_found['qatar_2022']:
            qatar_state = albums_found['qatar_2022'].get('user_state')
            self.log_test(
                "Qatar 2022 initially inactive", 
                qatar_state == 'inactive',
                f"Qatar 2022 state: {qatar_state}"
            )
            # Store Qatar album ID for later tests
            self.qatar_album_id = albums_found['qatar_2022'].get('id', self.qatar_album_id)
        else:
            self.log_test("Qatar 2022 album found", False, "Qatar 2022 album not found")
        
        return True

    def test_album_activation(self):
        """Test POST /api/albums/{album_id}/activate"""
        print("\n" + "="*60)
        print("TESTING ALBUM ACTIVATION")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping activation test - no auth token")
            return False
        
        # First, get albums to find FIFA 2026 ID
        success, albums = self.make_request("GET", "albums", expected_status=200)
        if not success:
            self.log_test("Get albums for activation test", False, albums)
            return False
        
        fifa_2026_id = None
        for album in albums:
            if 'FIFA' in album.get('name', '') and '2026' in album.get('name', ''):
                fifa_2026_id = album.get('id')
                break
        
        # Test 1: Try to activate FIFA 2026 (should fail)
        if fifa_2026_id:
            success, response = self.make_request(
                "POST", 
                f"albums/{fifa_2026_id}/activate", 
                expected_status=400
            )
            
            self.log_test(
                "FIFA 2026 activation blocked", 
                success,  # Should succeed in getting 400 error
                f"Correctly blocked with: {response}"
            )
        else:
            self.log_test("FIFA 2026 ID found", False, "Could not find FIFA 2026 album")
        
        # Test 2: Activate Qatar 2022 (should succeed)
        success, response = self.make_request(
            "POST", 
            f"albums/{self.qatar_album_id}/activate", 
            expected_status=200
        )
        
        self.log_test(
            "Qatar 2022 activation success", 
            success,
            str(response) if not success else "Album activated successfully"
        )
        
        if not success:
            return False
        
        # Test 3: Try to activate Qatar 2022 again (should fail)
        success, response = self.make_request(
            "POST", 
            f"albums/{self.qatar_album_id}/activate", 
            expected_status=400
        )
        
        self.log_test(
            "Duplicate activation blocked", 
            not success,  # Should fail with 400
            f"Correctly blocked with: {response}"
        )
        
        # Test 4: Verify Qatar 2022 is now ACTIVE
        success, albums = self.make_request("GET", "albums", expected_status=200)
        if success:
            qatar_album = next((a for a in albums if a.get('id') == self.qatar_album_id), None)
            if qatar_album:
                qatar_state = qatar_album.get('user_state')
                self.log_test(
                    "Qatar 2022 now ACTIVE", 
                    qatar_state == 'active',
                    f"Qatar 2022 state after activation: {qatar_state}"
                )
            else:
                self.log_test("Find Qatar 2022 after activation", False, "Album not found")
        
        return True

    def test_qatar_inventory(self):
        """Test GET /api/inventory?album_id={qatar_id} for Qatar 2022 catalog"""
        print("\n" + "="*60)
        print("TESTING QATAR 2022 INVENTORY")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping inventory test - no auth token")
            return False
        
        success, response = self.make_request(
            "GET", 
            f"inventory?album_id={self.qatar_album_id}", 
            expected_status=200
        )
        
        if not success:
            self.log_test("GET Qatar 2022 inventory", False, response)
            return False
        
        stickers = response
        
        # Test 1: Should return exactly 100 stickers
        self.log_test(
            "Qatar 2022 has 100 stickers", 
            len(stickers) == 100,
            f"Found {len(stickers)} stickers, expected 100"
        )
        
        # Test 2: All stickers should have required fields
        required_fields = ['number', 'name', 'team', 'category']
        all_have_fields = all(
            all(field in sticker for field in required_fields) 
            for sticker in stickers
        )
        
        self.log_test(
            "All stickers have required fields", 
            all_have_fields,
            "Some stickers missing required fields (number, name, team, category)"
        )
        
        # Test 3: Find Lionel Messi as sticker #61
        messi_sticker = next((s for s in stickers if s.get('number') == 61), None)
        
        if messi_sticker:
            is_messi = (
                messi_sticker.get('name') == 'Lionel Messi' and
                messi_sticker.get('team') == 'Argentina'
            )
            self.log_test(
                "Sticker #61 is Lionel Messi from Argentina", 
                is_messi,
                f"Sticker #61: {messi_sticker.get('name')} from {messi_sticker.get('team')}"
            )
        else:
            self.log_test("Find sticker #61", False, "Sticker #61 not found")
        
        # Test 4: Verify sticker numbers are sequential 1-100
        numbers = sorted([s.get('number') for s in stickers])
        sequential = numbers == list(range(1, 101))
        
        self.log_test(
            "Sticker numbers are sequential 1-100", 
            sequential,
            f"Number range: {min(numbers)}-{max(numbers)}, gaps: {set(range(1, 101)) - set(numbers)}"
        )
        
        # Test 5: Verify real team names (not dummy data)
        teams = set(s.get('team') for s in stickers)
        real_teams = {'Argentina', 'Brazil', 'England', 'France', 'Germany', 'Spain', 'Netherlands'}
        has_real_teams = len(real_teams.intersection(teams)) >= 3
        
        self.log_test(
            "Contains real team names", 
            has_real_teams,
            f"Found teams: {sorted(teams)}"
        )
        
        # Test 6: Verify owned_qty field is present (user inventory overlay)
        all_have_owned_qty = all('owned_qty' in sticker for sticker in stickers)
        
        self.log_test(
            "All stickers have owned_qty field", 
            all_have_owned_qty,
            "Some stickers missing owned_qty field"
        )
        
        return True

    def test_album_not_found(self):
        """Test inventory endpoint with invalid album ID"""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING")
        print("="*60)
        
        if not self.token:
            print("❌ Skipping error handling test - no auth token")
            return False
        
        # Test with invalid album ID
        fake_album_id = "00000000-0000-0000-0000-000000000000"
        success, response = self.make_request(
            "GET", 
            f"inventory?album_id={fake_album_id}", 
            expected_status=404
        )
        
        self.log_test(
            "Invalid album ID returns 404", 
            not success,  # Should fail with 404
            f"Correctly returned error: {response}"
        )
        
        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n🚀 Starting MisFigus Album States & Qatar 2022 Catalog Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Qatar Album ID: {self.qatar_album_id}")
        
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
            ("Albums Endpoint", self.test_albums_endpoint),
            ("Album Activation", self.test_album_activation),
            ("Qatar 2022 Inventory", self.test_qatar_inventory),
            ("Error Handling", self.test_album_not_found)
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
    tester = MisFigusAlbumTester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'qatar_album_id': tester.qatar_album_id,
        'token_obtained': tester.token is not None
    }
    
    try:
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/backend_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())