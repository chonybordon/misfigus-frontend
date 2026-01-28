import requests
import sys
import json
import time
from datetime import datetime

class MisFigusFixesTester:
    def __init__(self, base_url="https://sticker-swap-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.partner_token = None
        self.partner_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.qatar_album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"
        self.exchange_id = None
        self.chat_id = None

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

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use provided token or default token
        auth_token = token or self.token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

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

    def authenticate_user(self, email_suffix="user1"):
        """Authenticate a user and return token and user_id"""
        test_email = f"misfigus.test.{email_suffix}.{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com"
        
        print(f"🔍 Authenticating user: {test_email}")
        
        # Send OTP
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": test_email},
            200
        )
        
        if not success:
            return None, None, f"Failed to send OTP: {response}"
            
        # Check backend logs for OTP
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            log_lines = result.stdout.split('\n')
            otp_code = None
            
            # Look for the most recent OTP
            for line in reversed(log_lines):
                if "[OTP] OTP:" in line:
                    parts = line.split("[OTP] OTP:")
                    if len(parts) > 1:
                        otp_code = parts[1].strip()
                        break
            
            if otp_code:
                # Verify OTP
                success, response = self.make_request(
                    "POST",
                    "auth/verify-otp",
                    {"email": test_email, "otp": otp_code},
                    200
                )
                
                if success and 'token' in response:
                    return response['token'], response['user']['id'], None
                else:
                    return None, None, f"Failed to verify OTP: {response}"
            else:
                return None, None, "Could not find OTP in backend logs"
                
        except Exception as e:
            return None, None, f"Error checking logs: {e}"

    def setup_test_users(self):
        """Setup two test users for exchange testing"""
        print("\n" + "="*60)
        print("SETTING UP TEST USERS")
        print("="*60)
        
        # Authenticate first user
        self.token, self.user_id, error = self.authenticate_user("user1")
        if not self.token:
            self.log_test("Authenticate User 1", False, error)
            return False
        
        self.log_test("Authenticate User 1", True, f"User ID: {self.user_id}")
        
        # Authenticate second user
        self.partner_token, self.partner_user_id, error = self.authenticate_user("user2")
        if not self.partner_token:
            self.log_test("Authenticate User 2", False, error)
            return False
        
        self.log_test("Authenticate User 2", True, f"User ID: {self.partner_user_id}")
        
        # Activate Qatar album for both users
        for token, user_desc in [(self.token, "User 1"), (self.partner_token, "User 2")]:
            success, response = self.make_request(
                "POST", 
                f"albums/{self.qatar_album_id}/activate", 
                expected_status=200,
                token=token
            )
            
            self.log_test(f"Activate Qatar album for {user_desc}", success, str(response) if not success else "")
            
            if not success:
                return False
        
        # Setup inventory to create mutual matches
        # User 1: has duplicates of sticker 1, needs sticker 2
        # User 2: has duplicates of sticker 2, needs sticker 1
        
        # Get inventory to find sticker IDs
        success, inventory = self.make_request(
            "GET",
            f"inventory?album_id={self.qatar_album_id}",
            expected_status=200
        )
        
        if not success or not inventory:
            self.log_test("Get inventory for setup", False, "Could not get inventory")
            return False
        
        # Find first two stickers
        sticker_1_id = inventory[0]['id'] if len(inventory) > 0 else None
        sticker_2_id = inventory[1]['id'] if len(inventory) > 1 else None
        
        if not sticker_1_id or not sticker_2_id:
            self.log_test("Find stickers for setup", False, "Not enough stickers in inventory")
            return False
        
        # User 1: Set sticker 1 to 2 (duplicate), sticker 2 to 0 (missing)
        for sticker_id, qty in [(sticker_1_id, 2), (sticker_2_id, 0)]:
            success, response = self.make_request(
                "PUT",
                "inventory",
                {"sticker_id": sticker_id, "owned_qty": qty},
                200,
                token=self.token
            )
            if not success:
                self.log_test(f"Set User 1 inventory", False, response)
                return False
        
        # User 2: Set sticker 1 to 0 (missing), sticker 2 to 2 (duplicate)
        for sticker_id, qty in [(sticker_1_id, 0), (sticker_2_id, 2)]:
            success, response = self.make_request(
                "PUT",
                "inventory",
                {"sticker_id": sticker_id, "owned_qty": qty},
                200,
                token=self.partner_token
            )
            if not success:
                self.log_test(f"Set User 2 inventory", False, response)
                return False
        
        self.log_test("Setup mutual sticker matches", True, f"User 1 has {sticker_1_id}, needs {sticker_2_id}; User 2 has {sticker_2_id}, needs {sticker_1_id}")
        
        return True

    def test_fix_a_chat_i18n_system_message(self):
        """Test Fix A - Chat i18n system message stores key instead of English text"""
        print("\n" + "="*60)
        print("TESTING FIX A - CHAT I18N SYSTEM MESSAGE")
        print("="*60)
        
        if not self.token or not self.partner_token:
            print("❌ Skipping - need authenticated users")
            return False
        
        # Create an exchange to trigger system message
        success, response = self.make_request(
            "POST",
            f"albums/{self.qatar_album_id}/exchanges",
            {
                "album_id": self.qatar_album_id,
                "partner_user_id": self.partner_user_id
            },
            200
        )
        
        if not success:
            self.log_test("Create exchange for i18n test", False, response)
            return False
        
        self.exchange_id = response.get('exchange', {}).get('id')
        self.log_test("Create exchange for i18n test", True, f"Exchange ID: {self.exchange_id}")
        
        # Get the chat for this exchange
        success, chat_response = self.make_request(
            "GET",
            f"exchanges/{self.exchange_id}/chat",
            expected_status=200
        )
        
        if not success:
            self.log_test("Get chat for i18n test", False, chat_response)
            return False
        
        self.chat_id = chat_response.get('chat', {}).get('id')
        messages = chat_response.get('messages', [])
        
        # Find system message
        system_message = None
        for msg in messages:
            if msg.get('sender_id') == 'system':
                system_message = msg
                break
        
        if not system_message:
            self.log_test("Find system message", False, "No system message found")
            return False
        
        # Check that message content is an i18n key, not English text
        message_content = system_message.get('content', '')
        is_i18n_key = message_content == "SYSTEM_EXCHANGE_STARTED"
        
        self.log_test(
            "System message uses i18n key", 
            is_i18n_key,
            f"Message content: '{message_content}' (expected: 'SYSTEM_EXCHANGE_STARTED')"
        )
        
        return is_i18n_key

    def test_fix_bc_message_visibility_indicators(self):
        """Test Fix B & C - Message visibility indicators"""
        print("\n" + "="*60)
        print("TESTING FIX B & C - MESSAGE VISIBILITY INDICATORS")
        print("="*60)
        
        if not self.exchange_id or not self.chat_id:
            print("❌ Skipping - need existing exchange and chat")
            return False
        
        # Send a message from partner to user
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/chat/messages",
            {"content": "Hello, let's exchange stickers!"},
            200,
            token=self.partner_token
        )
        
        self.log_test("Send message from partner", success, str(response) if not success else "")
        
        if not success:
            return False
        
        # Test 1: GET /api/albums/{album_id}/exchanges should return has_unread and unread_count
        success, exchanges_response = self.make_request(
            "GET",
            f"albums/{self.qatar_album_id}/exchanges",
            expected_status=200
        )
        
        if not success:
            self.log_test("Get album exchanges", False, exchanges_response)
            return False
        
        exchanges = exchanges_response if isinstance(exchanges_response, list) else []
        
        # Find our exchange
        our_exchange = None
        for exchange in exchanges:
            if exchange.get('id') == self.exchange_id:
                our_exchange = exchange
                break
        
        if not our_exchange:
            self.log_test("Find our exchange in list", False, "Exchange not found in list")
            return False
        
        # Check has_unread and unread_count fields
        has_unread_field = 'has_unread' in our_exchange
        unread_count_field = 'unread_count' in our_exchange
        
        self.log_test("Exchange has has_unread field", has_unread_field, "")
        self.log_test("Exchange has unread_count field", unread_count_field, "")
        
        if has_unread_field and unread_count_field:
            has_unread = our_exchange.get('has_unread', False)
            unread_count = our_exchange.get('unread_count', 0)
            
            self.log_test(
                "Exchange shows unread messages", 
                has_unread and unread_count > 0,
                f"has_unread: {has_unread}, unread_count: {unread_count}"
            )
        
        # Test 2: GET /api/albums/{album_id} should return has_unread_exchanges and pending_exchanges
        success, album_response = self.make_request(
            "GET",
            f"albums/{self.qatar_album_id}",
            expected_status=200
        )
        
        if not success:
            self.log_test("Get album details", False, album_response)
            return False
        
        has_unread_exchanges_field = 'has_unread_exchanges' in album_response
        pending_exchanges_field = 'pending_exchanges' in album_response
        
        self.log_test("Album has has_unread_exchanges field", has_unread_exchanges_field, "")
        self.log_test("Album has pending_exchanges field", pending_exchanges_field, "")
        
        if has_unread_exchanges_field and pending_exchanges_field:
            has_unread_exchanges = album_response.get('has_unread_exchanges', False)
            pending_exchanges = album_response.get('pending_exchanges', 0)
            
            self.log_test(
                "Album shows unread exchanges", 
                has_unread_exchanges and pending_exchanges > 0,
                f"has_unread_exchanges: {has_unread_exchanges}, pending_exchanges: {pending_exchanges}"
            )
        
        # Test 3: GET /api/exchanges/{exchange_id}/chat should mark messages as read
        success, chat_response = self.make_request(
            "GET",
            f"exchanges/{self.exchange_id}/chat",
            expected_status=200
        )
        
        self.log_test("Get chat marks messages as read", success, str(chat_response) if not success else "")
        
        # After reading, check that unread count decreases
        time.sleep(1)  # Give time for read status to update
        
        success, exchanges_response_after = self.make_request(
            "GET",
            f"albums/{self.qatar_album_id}/exchanges",
            expected_status=200
        )
        
        if success:
            exchanges_after = exchanges_response_after if isinstance(exchanges_response_after, list) else []
            our_exchange_after = None
            for exchange in exchanges_after:
                if exchange.get('id') == self.exchange_id:
                    our_exchange_after = exchange
                    break
            
            if our_exchange_after:
                unread_count_after = our_exchange_after.get('unread_count', 0)
                self.log_test(
                    "Unread count decreased after reading", 
                    unread_count_after == 0,
                    f"Unread count after reading: {unread_count_after}"
                )
        
        return True

    def test_fix_e_exchange_upsert(self):
        """Test Fix E - Exchange already exists error (UPSERT behavior)"""
        print("\n" + "="*60)
        print("TESTING FIX E - EXCHANGE UPSERT BEHAVIOR")
        print("="*60)
        
        if not self.token or not self.partner_token:
            print("❌ Skipping - need authenticated users")
            return False
        
        # Try to create the SAME exchange again (should return existing with is_existing: true)
        success, response = self.make_request(
            "POST",
            f"albums/{self.qatar_album_id}/exchanges",
            {
                "album_id": self.qatar_album_id,
                "partner_user_id": self.partner_user_id
            },
            200
        )
        
        if not success:
            self.log_test("Create duplicate exchange", False, response)
            return False
        
        # Check that response indicates existing exchange
        is_existing = response.get('is_existing', False)
        exchange_data = response.get('exchange', {})
        
        self.log_test(
            "Duplicate exchange returns existing", 
            is_existing,
            f"is_existing: {is_existing}, exchange_id: {exchange_data.get('id')}"
        )
        
        # Verify it's the same exchange ID
        same_exchange = exchange_data.get('id') == self.exchange_id
        self.log_test(
            "Same exchange ID returned", 
            same_exchange,
            f"Original: {self.exchange_id}, Returned: {exchange_data.get('id')}"
        )
        
        return is_existing and same_exchange

    def test_fix_g_non_penalizing_failure_reasons(self):
        """Test Fix G - Non-penalizing failure reasons"""
        print("\n" + "="*60)
        print("TESTING FIX G - NON-PENALIZING FAILURE REASONS")
        print("="*60)
        
        if not self.exchange_id:
            print("❌ Skipping - need existing exchange")
            return False
        
        # Get user reputation before failure
        success, rep_before = self.make_request(
            "GET",
            "user/reputation",
            expected_status=[200, 404],  # 404 if no reputation record yet
            token=self.token
        )
        
        initial_failed_exchanges = 0
        if success and rep_before:
            initial_failed_exchanges = rep_before.get('failed_exchanges', 0)
        
        # Confirm exchange with failure_reason="schedule_conflict" (minor reason)
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/confirm",
            {
                "confirmed": False,
                "failure_reason": "schedule_conflict"
            },
            200
        )
        
        self.log_test(
            "Confirm exchange with minor failure reason", 
            success,
            str(response) if not success else "schedule_conflict accepted"
        )
        
        if not success:
            return False
        
        # Check that reputation was NOT negatively affected
        time.sleep(1)  # Give time for reputation update
        
        success, rep_after = self.make_request(
            "GET",
            "user/reputation",
            expected_status=200,
            token=self.token
        )
        
        if not success:
            self.log_test("Get reputation after minor failure", False, rep_after)
            return False
        
        final_failed_exchanges = rep_after.get('failed_exchanges', 0)
        
        # Minor failure should NOT increase failed_exchanges count
        reputation_unchanged = final_failed_exchanges == initial_failed_exchanges
        
        self.log_test(
            "Minor failure doesn't affect reputation", 
            reputation_unchanged,
            f"Failed exchanges before: {initial_failed_exchanges}, after: {final_failed_exchanges}"
        )
        
        return reputation_unchanged

    def run_all_tests(self):
        """Run all fix tests in sequence"""
        print(f"\n🚀 Starting MisFigus Fixes Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Setup test users first
        if not self.setup_test_users():
            print("❌ Failed to setup test users")
            return False
        
        # Run fix tests
        tests = [
            ("Fix A - Chat i18n system message", self.test_fix_a_chat_i18n_system_message),
            ("Fix B & C - Message visibility indicators", self.test_fix_bc_message_visibility_indicators),
            ("Fix E - Exchange UPSERT behavior", self.test_fix_e_exchange_upsert),
            ("Fix G - Non-penalizing failure reasons", self.test_fix_g_non_penalizing_failure_reasons)
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
    tester = MisFigusFixesTester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'exchange_id': tester.exchange_id,
        'chat_id': tester.chat_id
    }
    
    try:
        with open('/app/misfigus_fixes_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/misfigus_fixes_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())