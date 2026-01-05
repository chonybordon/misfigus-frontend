import requests
import sys
import json
import time
from datetime import datetime

class MisFigusExchangeTester:
    def __init__(self, base_url="https://swap-stickers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.qatar_album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"
        
        # Test users
        self.user1_token = None
        self.user1_id = None
        self.user2_token = None
        self.user2_id = None
        
        # Exchange data
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
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

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

    def authenticate_user(self, user_suffix):
        """Authenticate a test user and return token and user_id"""
        test_email = f"exchange-test-user-{user_suffix}@misfigus.com"
        
        print(f"🔍 Authenticating user: {test_email}")
        
        # Send OTP
        success, response = self.make_request(
            "POST", 
            "auth/send-otp", 
            {"email": test_email},
            200
        )
        
        if not success:
            print(f"❌ Failed to send OTP for {test_email}: {response}")
            return None, None
            
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
                print(f"✅ Found OTP in logs: {otp_code}")
                
                # Verify OTP
                success, response = self.make_request(
                    "POST",
                    "auth/verify-otp",
                    {"email": test_email, "otp": otp_code},
                    200
                )
                
                if success and 'token' in response:
                    token = response['token']
                    user_id = response['user']['id']
                    print(f"✅ Authentication successful! User ID: {user_id}")
                    return token, user_id
                    
        except Exception as e:
            print(f"❌ Error checking logs: {e}")
            
        return None, None

    def setup_test_users(self):
        """Setup two test users for exchange testing"""
        print("\n" + "="*60)
        print("SETTING UP TEST USERS")
        print("="*60)
        
        # Authenticate user 1
        self.user1_token, self.user1_id = self.authenticate_user("1")
        if not self.user1_token:
            self.log_test("Authenticate User 1", False, "Failed to authenticate user 1")
            return False
        self.log_test("Authenticate User 1", True, f"User ID: {self.user1_id}")
        
        # Authenticate user 2
        self.user2_token, self.user2_id = self.authenticate_user("2")
        if not self.user2_token:
            self.log_test("Authenticate User 2", False, "Failed to authenticate user 2")
            return False
        self.log_test("Authenticate User 2", True, f"User ID: {self.user2_id}")
        
        # Activate Qatar album for both users
        for i, (token, user_id) in enumerate([(self.user1_token, self.user1_id), (self.user2_token, self.user2_id)], 1):
            success, response = self.make_request(
                "POST", 
                f"albums/{self.qatar_album_id}/activate", 
                expected_status=200,
                token=token
            )
            self.log_test(f"Activate Qatar album for User {i}", success, str(response) if not success else "")
            if not success:
                return False
        
        return True

    def setup_test_inventory(self):
        """Setup test inventory for both users to create mutual matches"""
        print("\n" + "="*60)
        print("SETTING UP TEST INVENTORY")
        print("="*60)
        
        # Get stickers for Qatar album
        success, stickers = self.make_request(
            "GET", 
            f"inventory?album_id={self.qatar_album_id}",
            token=self.user1_token
        )
        
        if not success:
            self.log_test("Get Qatar stickers", False, stickers)
            return False
        
        self.log_test("Get Qatar stickers", True, f"Found {len(stickers)} stickers")
        
        if len(stickers) < 10:
            self.log_test("Sufficient stickers for testing", False, f"Only {len(stickers)} stickers found")
            return False
        
        # User 1: Give duplicates of stickers 1-5, missing 6-10
        for i in range(1, 6):
            sticker = next((s for s in stickers if s.get('number') == i), None)
            if sticker:
                success, response = self.make_request(
                    "PUT",
                    "inventory",
                    {"sticker_id": sticker['id'], "owned_qty": 2},
                    token=self.user1_token
                )
                if not success:
                    self.log_test(f"Set User 1 sticker {i} to 2", False, response)
                    return False
        
        # User 2: Give duplicates of stickers 6-10, missing 1-5
        for i in range(6, 11):
            sticker = next((s for s in stickers if s.get('number') == i), None)
            if sticker:
                success, response = self.make_request(
                    "PUT",
                    "inventory",
                    {"sticker_id": sticker['id'], "owned_qty": 2},
                    token=self.user2_token
                )
                if not success:
                    self.log_test(f"Set User 2 sticker {i} to 2", False, response)
                    return False
        
        self.log_test("Setup mutual match inventory", True, "User 1 has 1-5 duplicates, User 2 has 6-10 duplicates")
        return True

    def test_create_exchange(self):
        """Test POST /api/albums/{albumId}/exchanges"""
        print("\n" + "="*60)
        print("TESTING EXCHANGE CREATION")
        print("="*60)
        
        # Test 1: Create exchange between user1 and user2
        success, response = self.make_request(
            "POST",
            f"albums/{self.qatar_album_id}/exchanges",
            {
                "album_id": self.qatar_album_id,
                "partner_user_id": self.user2_id
            },
            token=self.user1_token
        )
        
        if success and 'exchange' in response:
            self.exchange_id = response['exchange']['id']
            self.log_test("Create exchange", True, f"Exchange ID: {self.exchange_id}")
            
            # Verify exchange details
            exchange = response['exchange']
            
            # Check status is pending
            status_correct = exchange.get('status') == 'pending'
            self.log_test("Exchange status is pending", status_correct, f"Status: {exchange.get('status')}")
            
            # Check users are correct
            users_correct = (
                exchange.get('user_a_id') == self.user1_id and 
                exchange.get('user_b_id') == self.user2_id
            )
            self.log_test("Exchange users correct", users_correct, f"User A: {exchange.get('user_a_id')}, User B: {exchange.get('user_b_id')}")
            
            # Check offers exist
            offers_exist = (
                len(exchange.get('user_a_offers', [])) > 0 and 
                len(exchange.get('user_b_offers', [])) > 0
            )
            self.log_test("Exchange offers exist", offers_exist, f"User A offers: {len(exchange.get('user_a_offers', []))}, User B offers: {len(exchange.get('user_b_offers', []))}")
            
        else:
            self.log_test("Create exchange", False, response)
            return False
        
        # Test 2: Try to create duplicate exchange (should fail)
        success, response = self.make_request(
            "POST",
            f"albums/{self.qatar_album_id}/exchanges",
            {
                "album_id": self.qatar_album_id,
                "partner_user_id": self.user2_id
            },
            expected_status=400,
            token=self.user1_token
        )
        
        self.log_test("Duplicate exchange blocked", success, f"Correctly blocked: {response}")
        
        return True

    def test_get_exchanges(self):
        """Test GET /api/albums/{albumId}/exchanges"""
        print("\n" + "="*60)
        print("TESTING GET USER EXCHANGES")
        print("="*60)
        
        # Test 1: Get exchanges for user 1
        success, response = self.make_request(
            "GET",
            f"albums/{self.qatar_album_id}/exchanges",
            token=self.user1_token
        )
        
        if success:
            exchanges = response
            self.log_test("Get User 1 exchanges", True, f"Found {len(exchanges)} exchanges")
            
            # Check exchange is in the list
            exchange_found = any(ex.get('id') == self.exchange_id for ex in exchanges)
            self.log_test("Exchange found in User 1 list", exchange_found, "Exchange not found in list")
            
            if exchanges:
                exchange = exchanges[0]
                # Check partner info is included
                partner_info_exists = 'partner' in exchange
                self.log_test("Partner info included", partner_info_exists, "Partner info missing")
                
                # Check is_user_a flag
                is_user_a_correct = exchange.get('is_user_a') == True
                self.log_test("is_user_a flag correct for User 1", is_user_a_correct, f"is_user_a: {exchange.get('is_user_a')}")
        else:
            self.log_test("Get User 1 exchanges", False, response)
            return False
        
        # Test 2: Get exchanges for user 2
        success, response = self.make_request(
            "GET",
            f"albums/{self.qatar_album_id}/exchanges",
            token=self.user2_token
        )
        
        if success:
            exchanges = response
            self.log_test("Get User 2 exchanges", True, f"Found {len(exchanges)} exchanges")
            
            if exchanges:
                exchange = exchanges[0]
                # Check is_user_a flag
                is_user_a_correct = exchange.get('is_user_a') == False
                self.log_test("is_user_a flag correct for User 2", is_user_a_correct, f"is_user_a: {exchange.get('is_user_a')}")
        else:
            self.log_test("Get User 2 exchanges", False, response)
        
        return True

    def test_exchange_detail(self):
        """Test GET /api/exchanges/{exchangeId}"""
        print("\n" + "="*60)
        print("TESTING EXCHANGE DETAIL")
        print("="*60)
        
        if not self.exchange_id:
            self.log_test("Exchange detail test", False, "No exchange ID available")
            return False
        
        # Test 1: Get exchange detail as user 1
        success, response = self.make_request(
            "GET",
            f"exchanges/{self.exchange_id}",
            token=self.user1_token
        )
        
        if success:
            exchange = response
            self.log_test("Get exchange detail", True, f"Exchange ID: {exchange.get('id')}")
            
            # Check all required fields are present
            required_fields = ['id', 'status', 'user_a_id', 'user_b_id', 'partner', 'is_user_a']
            fields_present = all(field in exchange for field in required_fields)
            self.log_test("All required fields present", fields_present, f"Missing fields: {[f for f in required_fields if f not in exchange]}")
            
            # Check sticker details are enriched
            sticker_details_exist = (
                'user_a_offers_details' in exchange and 
                'user_b_offers_details' in exchange
            )
            self.log_test("Sticker details enriched", sticker_details_exist, "Sticker details missing")
            
        else:
            self.log_test("Get exchange detail", False, response)
            return False
        
        # Test 3: Try to access exchange as unauthorized user (should fail)
        # First create a third user
        user3_token, user3_id = self.authenticate_user("3")
        if user3_token:
            success, response = self.make_request(
                "GET",
                f"exchanges/{self.exchange_id}",
                expected_status=403,
                token=user3_token
            )
            self.log_test("Unauthorized access blocked", success, f"Correctly blocked: {response}")
        
        return True

    def test_exchange_chat(self):
        """Test GET/POST /api/exchanges/{exchangeId}/chat"""
        print("\n" + "="*60)
        print("TESTING EXCHANGE CHAT")
        print("="*60)
        
        if not self.exchange_id:
            self.log_test("Exchange chat test", False, "No exchange ID available")
            return False
        
        # Test 1: Get initial chat (should have system message)
        success, response = self.make_request(
            "GET",
            f"exchanges/{self.exchange_id}/chat",
            token=self.user1_token
        )
        
        if success:
            chat_data = response
            self.log_test("Get exchange chat", True, f"Chat ID: {chat_data.get('chat', {}).get('id')}")
            
            # Check system message exists
            messages = chat_data.get('messages', [])
            system_message_exists = any(msg.get('is_system') for msg in messages)
            self.log_test("System message exists", system_message_exists, "No system message found")
            
            # Check chat is not read-only (exchange is pending)
            is_read_only = chat_data.get('is_read_only', True)
            self.log_test("Chat is not read-only", not is_read_only, f"is_read_only: {is_read_only}")
            
        else:
            self.log_test("Get exchange chat", False, response)
            return False
        
        # Test 2: Send a chat message
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/chat/messages",
            {"content": "Hello! Let's coordinate our exchange."},
            token=self.user1_token
        )
        
        if success:
            message = response
            self.log_test("Send chat message", True, f"Message ID: {message.get('id')}")
            
            # Check message fields
            message_valid = (
                message.get('sender_id') == self.user1_id and
                message.get('content') == "Hello! Let's coordinate our exchange." and
                message.get('is_system') == False
            )
            self.log_test("Message fields correct", message_valid, f"Message: {message}")
            
        else:
            self.log_test("Send chat message", False, response)
            return False
        
        # Test 3: User 2 sends a reply
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/chat/messages",
            {"content": "Great! When and where should we meet?"},
            token=self.user2_token
        )
        
        self.log_test("User 2 sends reply", success, str(response) if not success else "Reply sent successfully")
        
        # Test 4: Verify both messages are in chat
        success, response = self.make_request(
            "GET",
            f"exchanges/{self.exchange_id}/chat",
            token=self.user1_token
        )
        
        if success:
            messages = response.get('messages', [])
            user_messages = [msg for msg in messages if not msg.get('is_system')]
            self.log_test("Both user messages in chat", len(user_messages) >= 2, f"Found {len(user_messages)} user messages")
        
        return True

    def test_exchange_confirmation(self):
        """Test POST /api/exchanges/{exchangeId}/confirm"""
        print("\n" + "="*60)
        print("TESTING EXCHANGE CONFIRMATION")
        print("="*60)
        
        if not self.exchange_id:
            self.log_test("Exchange confirmation test", False, "No exchange ID available")
            return False
        
        # Test 1: User 1 confirms thumbs up
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/confirm",
            {"confirmed": True},
            token=self.user1_token
        )
        
        if success:
            self.log_test("User 1 confirms thumbs up", True, f"Response: {response}")
            
            # Check status is still pending (waiting for user 2)
            status = response.get('status')
            self.log_test("Status still pending after one confirmation", status == 'pending', f"Status: {status}")
            
        else:
            self.log_test("User 1 confirms thumbs up", False, response)
            return False
        
        # Test 2: Try to confirm again (should fail)
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/confirm",
            {"confirmed": True},
            expected_status=400,
            token=self.user1_token
        )
        
        self.log_test("Duplicate confirmation blocked", success, f"Correctly blocked: {response}")
        
        # Test 3: User 2 confirms thumbs up (should complete exchange)
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/confirm",
            {"confirmed": True},
            token=self.user2_token
        )
        
        if success:
            self.log_test("User 2 confirms thumbs up", True, f"Response: {response}")
            
            # Check status is now completed
            status = response.get('status')
            self.log_test("Exchange status completed", status == 'completed', f"Status: {status}")
            
        else:
            self.log_test("User 2 confirms thumbs up", False, response)
            return False
        
        # Test 4: Verify chat is now read-only
        success, response = self.make_request(
            "GET",
            f"exchanges/{self.exchange_id}/chat",
            token=self.user1_token
        )
        
        if success:
            is_read_only = response.get('is_read_only', False)
            self.log_test("Chat is now read-only", is_read_only, f"is_read_only: {is_read_only}")
            
            # Check for completion system message
            messages = response.get('messages', [])
            completion_message = any(
                msg.get('is_system') and '✅' in msg.get('content', '') 
                for msg in messages
            )
            self.log_test("Completion system message added", completion_message, "No completion message found")
        
        # Test 5: Try to send message to closed chat (should fail)
        success, response = self.make_request(
            "POST",
            f"exchanges/{self.exchange_id}/chat/messages",
            {"content": "This should fail"},
            expected_status=400,
            token=self.user1_token
        )
        
        self.log_test("Message to closed chat blocked", success, f"Correctly blocked: {response}")
        
        return True

    def test_reputation_system(self):
        """Test GET /api/user/reputation"""
        print("\n" + "="*60)
        print("TESTING REPUTATION SYSTEM")
        print("="*60)
        
        # Test 1: Get User 1 reputation
        success, response = self.make_request(
            "GET",
            "user/reputation",
            token=self.user1_token
        )
        
        if success:
            reputation = response
            self.log_test("Get User 1 reputation", True, f"Status: {reputation.get('status')}")
            
            # Check reputation fields
            required_fields = ['user_id', 'total_exchanges', 'successful_exchanges', 'failed_exchanges', 'status']
            fields_present = all(field in reputation for field in required_fields)
            self.log_test("Reputation fields present", fields_present, f"Missing: {[f for f in required_fields if f not in reputation]}")
            
            # Check successful exchange was recorded
            total_exchanges = reputation.get('total_exchanges', 0)
            successful_exchanges = reputation.get('successful_exchanges', 0)
            
            self.log_test("Exchange recorded in reputation", total_exchanges >= 1, f"Total exchanges: {total_exchanges}")
            self.log_test("Successful exchange recorded", successful_exchanges >= 1, f"Successful exchanges: {successful_exchanges}")
            
            # Check status is trusted
            status = reputation.get('status')
            self.log_test("Reputation status is trusted", status == 'trusted', f"Status: {status}")
            
        else:
            self.log_test("Get User 1 reputation", False, response)
            return False
        
        # Test 2: Get User 2 reputation
        success, response = self.make_request(
            "GET",
            "user/reputation",
            token=self.user2_token
        )
        
        if success:
            reputation = response
            self.log_test("Get User 2 reputation", True, f"Status: {reputation.get('status')}")
            
            # Check User 2 also has updated reputation
            total_exchanges = reputation.get('total_exchanges', 0)
            successful_exchanges = reputation.get('successful_exchanges', 0)
            
            self.log_test("User 2 exchange recorded", total_exchanges >= 1, f"Total exchanges: {total_exchanges}")
            self.log_test("User 2 successful exchange recorded", successful_exchanges >= 1, f"Successful exchanges: {successful_exchanges}")
            
        else:
            self.log_test("Get User 2 reputation", False, response)
        
        return True

    def test_failed_exchange_scenario(self):
        """Test exchange failure scenario and reputation impact"""
        print("\n" + "="*60)
        print("TESTING FAILED EXCHANGE SCENARIO")
        print("="*60)
        
        # Create a new exchange for failure testing
        success, response = self.make_request(
            "POST",
            f"albums/{self.qatar_album_id}/exchanges",
            {
                "album_id": self.qatar_album_id,
                "partner_user_id": self.user1_id
            },
            token=self.user2_token
        )
        
        if not success:
            self.log_test("Create second exchange", False, response)
            return False
        
        failed_exchange_id = response['exchange']['id']
        self.log_test("Create second exchange", True, f"Exchange ID: {failed_exchange_id}")
        
        # User 2 confirms thumbs down with failure reason
        success, response = self.make_request(
            "POST",
            f"exchanges/{failed_exchange_id}/confirm",
            {
                "confirmed": False,
                "failure_reason": "no_show"
            },
            token=self.user2_token
        )
        
        if success:
            self.log_test("User 2 confirms thumbs down", True, f"Response: {response}")
            
            # Check status is failed immediately
            status = response.get('status')
            self.log_test("Exchange failed immediately", status == 'failed', f"Status: {status}")
            
        else:
            self.log_test("User 2 confirms thumbs down", False, response)
            return False
        
        # Check reputation was updated for both users
        for i, token in enumerate([self.user1_token, self.user2_token], 1):
            success, response = self.make_request(
                "GET",
                "user/reputation",
                token=token
            )
            
            if success:
                reputation = response
                failed_exchanges = reputation.get('failed_exchanges', 0)
                self.log_test(f"User {i} failed exchange recorded", failed_exchanges >= 1, f"Failed exchanges: {failed_exchanges}")
            else:
                self.log_test(f"Get User {i} reputation after failure", False, response)
        
        return True

    def run_all_tests(self):
        """Run all exchange tests in sequence"""
        print(f"\n🚀 Starting MisFigus Exchange Lifecycle and Reputation System Tests")
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
            ("Setup Test Users", self.setup_test_users),
            ("Setup Test Inventory", self.setup_test_inventory),
            ("Create Exchange", self.test_create_exchange),
            ("Get User Exchanges", self.test_get_exchanges),
            ("Exchange Detail", self.test_exchange_detail),
            ("Exchange Chat", self.test_exchange_chat),
            ("Exchange Confirmation", self.test_exchange_confirmation),
            ("Reputation System", self.test_reputation_system),
            ("Failed Exchange Scenario", self.test_failed_exchange_scenario)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔄 Running {test_name}...")
            try:
                result = test_func()
                if not result:
                    print(f"⚠️  {test_name} failed, but continuing with remaining tests...")
            except Exception as e:
                self.log_test(f"{test_name} (Exception)", False, str(e))
                print(f"⚠️  Exception in {test_name}: {e}")
        
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
    tester = MisFigusExchangeTester()
    success = tester.run_all_tests()
    
    # Save detailed test results
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': tester.tests_run,
        'tests_passed': tester.tests_passed,
        'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        'results': tester.test_results,
        'exchange_id': tester.exchange_id,
        'user1_id': tester.user1_id,
        'user2_id': tester.user2_id
    }
    
    try:
        with open('/app/exchange_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to /app/exchange_test_results.json")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())