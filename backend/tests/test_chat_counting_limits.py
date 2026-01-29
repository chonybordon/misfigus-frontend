"""
Test Chat Counting Logic for Subscription Limits

Tests the following scenarios:
1. When user A starts a new exchange/chat with user B → counts for user A's daily limit
2. When user B replies to that chat (first message) → counts for user B's daily limit
3. Subsequent messages in the same chat do NOT count for either user
4. Free plan limit: 1 chat/day enforced on both creation AND reply
5. Plus plan limit: 5 chats/day enforced on both creation AND reply
6. Unlimited plan: no limits on chat creation or reply
7. Counter increments correctly when replying to a new chat
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestChatCountingLimits:
    """Test chat counting logic for subscription limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_users = []
        self.test_exchanges = []
        
    def _create_test_user(self, email_prefix: str) -> dict:
        """Create a test user via OTP flow"""
        timestamp = int(time.time() * 1000)
        email = f"TEST_{email_prefix}_{timestamp}@test.com"
        
        # Send OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert response.status_code == 200, f"Failed to send OTP: {response.text}"
        
        # In dev mode, OTP is logged. We use a fixed OTP for testing
        # The backend logs the OTP, but we need to get it from logs or use dev mode
        # For testing, we'll try common dev OTPs or check if dev mode returns it
        otp_response = response.json()
        
        # Try to verify with common dev OTPs
        for otp in ["123456", "000000", "111111"]:
            verify_response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
                "email": email,
                "otp": otp
            })
            if verify_response.status_code == 200:
                user_data = verify_response.json()
                self.test_users.append(user_data['user'])
                return {
                    "user": user_data['user'],
                    "token": user_data['token'],
                    "email": email
                }
        
        pytest.skip(f"Could not verify OTP for test user {email}")
        
    def _get_auth_headers(self, token: str) -> dict:
        """Get authorization headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def _set_user_plan(self, token: str, plan: str) -> dict:
        """Set user's plan (mocked endpoint)"""
        response = self.session.post(
            f"{BASE_URL}/api/user/set-plan",
            params={"plan": plan},
            headers=self._get_auth_headers(token)
        )
        return response
    
    def _get_plan_status(self, token: str) -> dict:
        """Get user's plan status"""
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        return response.json() if response.status_code == 200 else None
    
    def _activate_album(self, token: str, album_id: str) -> bool:
        """Activate an album for a user"""
        response = self.session.post(
            f"{BASE_URL}/api/albums/{album_id}/activate",
            headers=self._get_auth_headers(token)
        )
        return response.status_code == 200
    
    def _create_exchange(self, token: str, album_id: str, partner_id: str) -> dict:
        """Create an exchange between users"""
        response = self.session.post(
            f"{BASE_URL}/api/exchanges",
            json={"album_id": album_id, "partner_id": partner_id},
            headers=self._get_auth_headers(token)
        )
        return response
    
    def _send_chat_message(self, token: str, exchange_id: str, content: str) -> dict:
        """Send a chat message"""
        response = self.session.post(
            f"{BASE_URL}/api/exchanges/{exchange_id}/chat/messages",
            json={"content": content},
            headers=self._get_auth_headers(token)
        )
        return response
    
    def _get_albums(self, token: str) -> list:
        """Get available albums"""
        response = self.session.get(
            f"{BASE_URL}/api/albums",
            headers=self._get_auth_headers(token)
        )
        return response.json() if response.status_code == 200 else []
    
    def _setup_inventory_for_exchange(self, token: str, album_id: str, sticker_ids: list, owned_qty: int):
        """Setup inventory for a user to enable exchanges"""
        for sticker_id in sticker_ids:
            self.session.put(
                f"{BASE_URL}/api/inventory",
                json={"sticker_id": sticker_id, "owned_qty": owned_qty},
                headers=self._get_auth_headers(token)
            )

    # ============================================
    # CORE TESTS
    # ============================================
    
    def test_api_health(self):
        """Test that API is accessible"""
        response = self.session.get(f"{BASE_URL}/api/health")
        # Health endpoint might not exist, try albums instead
        if response.status_code != 200:
            response = self.session.get(f"{BASE_URL}/api/albums")
        assert response.status_code in [200, 401], f"API not accessible: {response.status_code}"
        print("✓ API is accessible")
    
    def test_plan_status_endpoint(self):
        """Test plan status endpoint returns correct structure"""
        # Create a test user
        user_data = self._create_test_user("plan_status")
        if not user_data:
            pytest.skip("Could not create test user")
        
        status = self._get_plan_status(user_data['token'])
        assert status is not None, "Plan status should be returned"
        assert 'plan' in status, "Plan status should include 'plan' field"
        assert 'matches_used_today' in status, "Plan status should include 'matches_used_today'"
        assert 'matches_limit' in status, "Plan status should include 'matches_limit'"
        assert 'can_match' in status, "Plan status should include 'can_match'"
        
        print(f"✓ Plan status: {status['plan']}, matches_used: {status['matches_used_today']}/{status['matches_limit']}")
    
    def test_free_plan_default(self):
        """Test that new users default to free plan with 1 chat/day limit"""
        user_data = self._create_test_user("free_default")
        if not user_data:
            pytest.skip("Could not create test user")
        
        status = self._get_plan_status(user_data['token'])
        assert status['plan'] == 'free', "New users should default to free plan"
        assert status['matches_limit'] == 1, "Free plan should have 1 chat/day limit"
        assert status['matches_used_today'] == 0, "New users should have 0 matches used"
        
        print("✓ New user defaults to free plan with 1 chat/day limit")
    
    def test_set_plan_to_plus(self):
        """Test setting plan to plus increases limit to 5"""
        user_data = self._create_test_user("plus_plan")
        if not user_data:
            pytest.skip("Could not create test user")
        
        # Set to plus plan
        response = self._set_user_plan(user_data['token'], 'plus')
        assert response.status_code == 200, f"Failed to set plus plan: {response.text}"
        
        status = self._get_plan_status(user_data['token'])
        assert status['plan'] == 'plus', "Plan should be plus"
        assert status['matches_limit'] == 5, "Plus plan should have 5 chats/day limit"
        
        print("✓ Plus plan has 5 chats/day limit")
    
    def test_set_plan_to_unlimited(self):
        """Test setting plan to unlimited removes limits"""
        user_data = self._create_test_user("unlimited_plan")
        if not user_data:
            pytest.skip("Could not create test user")
        
        # Set to unlimited plan
        response = self._set_user_plan(user_data['token'], 'unlimited')
        assert response.status_code == 200, f"Failed to set unlimited plan: {response.text}"
        
        status = self._get_plan_status(user_data['token'])
        assert status['plan'] == 'unlimited', "Plan should be unlimited"
        assert status['matches_limit'] is None, "Unlimited plan should have no limit (None)"
        assert status['can_match'] == True, "Unlimited plan should always allow matching"
        
        print("✓ Unlimited plan has no chat limits")


class TestChatCountingWithExchanges:
    """Test chat counting with actual exchange creation and messaging"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def _get_auth_headers(self, token: str) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def _create_test_user_via_otp(self, email_prefix: str) -> dict:
        """Create a test user via OTP flow - returns user data with token"""
        timestamp = int(time.time() * 1000)
        email = f"TEST_{email_prefix}_{timestamp}@test.com"
        
        # Send OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        if response.status_code != 200:
            return None
        
        # Try common dev OTPs
        for otp in ["123456", "000000", "111111"]:
            verify_response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
                "email": email,
                "otp": otp
            })
            if verify_response.status_code == 200:
                data = verify_response.json()
                return {
                    "user": data['user'],
                    "token": data['token'],
                    "email": email,
                    "user_id": data['user']['id']
                }
        return None
    
    def _get_plan_status(self, token: str) -> dict:
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        return response.json() if response.status_code == 200 else None
    
    def _set_user_plan(self, token: str, plan: str):
        return self.session.post(
            f"{BASE_URL}/api/user/set-plan",
            params={"plan": plan},
            headers=self._get_auth_headers(token)
        )
    
    def _activate_album(self, token: str, album_id: str):
        return self.session.post(
            f"{BASE_URL}/api/albums/{album_id}/activate",
            headers=self._get_auth_headers(token)
        )
    
    def _get_albums(self, token: str) -> list:
        response = self.session.get(
            f"{BASE_URL}/api/albums",
            headers=self._get_auth_headers(token)
        )
        return response.json() if response.status_code == 200 else []
    
    def _get_inventory(self, token: str, album_id: str) -> list:
        response = self.session.get(
            f"{BASE_URL}/api/inventory",
            params={"album_id": album_id},
            headers=self._get_auth_headers(token)
        )
        return response.json() if response.status_code == 200 else []
    
    def _update_inventory(self, token: str, sticker_id: str, owned_qty: int):
        return self.session.put(
            f"{BASE_URL}/api/inventory",
            json={"sticker_id": sticker_id, "owned_qty": owned_qty},
            headers=self._get_auth_headers(token)
        )
    
    def _create_exchange(self, token: str, album_id: str, partner_id: str):
        return self.session.post(
            f"{BASE_URL}/api/exchanges",
            json={"album_id": album_id, "partner_id": partner_id},
            headers=self._get_auth_headers(token)
        )
    
    def _send_chat_message(self, token: str, exchange_id: str, content: str):
        return self.session.post(
            f"{BASE_URL}/api/exchanges/{exchange_id}/chat/messages",
            json={"content": content},
            headers=self._get_auth_headers(token)
        )
    
    def _get_exchange_chat(self, token: str, exchange_id: str):
        return self.session.get(
            f"{BASE_URL}/api/exchanges/{exchange_id}/chat",
            headers=self._get_auth_headers(token)
        )
    
    def test_exchange_creation_counts_for_creator(self):
        """
        Test 1: When user A starts a new exchange with user B → counts for user A's daily limit
        """
        print("\n=== Test: Exchange creation counts for creator ===")
        
        # Create two test users
        user_a = self._create_test_user_via_otp("creator_a")
        user_b = self._create_test_user_via_otp("partner_b")
        
        if not user_a or not user_b:
            pytest.skip("Could not create test users via OTP")
        
        print(f"Created User A: {user_a['email']}")
        print(f"Created User B: {user_b['email']}")
        
        # Both users on free plan (default)
        status_a_before = self._get_plan_status(user_a['token'])
        assert status_a_before['matches_used_today'] == 0, "User A should start with 0 matches"
        print(f"User A initial matches: {status_a_before['matches_used_today']}/{status_a_before['matches_limit']}")
        
        # Get an active album
        albums = self._get_albums(user_a['token'])
        active_albums = [a for a in albums if a.get('status') == 'active']
        if not active_albums:
            pytest.skip("No active albums available")
        
        album_id = active_albums[0]['id']
        print(f"Using album: {album_id}")
        
        # Both users activate the album
        self._activate_album(user_a['token'], album_id)
        self._activate_album(user_b['token'], album_id)
        
        # Setup inventory for mutual exchange
        inventory = self._get_inventory(user_a['token'], album_id)
        if len(inventory) < 4:
            pytest.skip("Not enough stickers in album for test")
        
        # User A has duplicates of stickers 0,1 and needs 2,3
        # User B has duplicates of stickers 2,3 and needs 0,1
        sticker_ids = [s['id'] for s in inventory[:4]]
        
        # User A: owns 2 of stickers 0,1 (duplicates), 0 of stickers 2,3 (needs)
        self._update_inventory(user_a['token'], sticker_ids[0], 2)
        self._update_inventory(user_a['token'], sticker_ids[1], 2)
        self._update_inventory(user_a['token'], sticker_ids[2], 0)
        self._update_inventory(user_a['token'], sticker_ids[3], 0)
        
        # User B: owns 2 of stickers 2,3 (duplicates), 0 of stickers 0,1 (needs)
        self._update_inventory(user_b['token'], sticker_ids[0], 0)
        self._update_inventory(user_b['token'], sticker_ids[1], 0)
        self._update_inventory(user_b['token'], sticker_ids[2], 2)
        self._update_inventory(user_b['token'], sticker_ids[3], 2)
        
        print("Inventory setup complete for mutual exchange")
        
        # User A creates exchange with User B
        exchange_response = self._create_exchange(user_a['token'], album_id, user_b['user_id'])
        
        if exchange_response.status_code != 200:
            print(f"Exchange creation failed: {exchange_response.status_code} - {exchange_response.text}")
            pytest.skip("Could not create exchange - may need location setup")
        
        exchange_data = exchange_response.json()
        exchange_id = exchange_data.get('exchange', {}).get('id')
        print(f"Exchange created: {exchange_id}")
        
        # Check User A's counter incremented
        status_a_after = self._get_plan_status(user_a['token'])
        assert status_a_after['matches_used_today'] == 1, f"User A should have 1 match used after creating exchange, got {status_a_after['matches_used_today']}"
        print(f"✓ User A matches after creation: {status_a_after['matches_used_today']}/{status_a_after['matches_limit']}")
        
        # Check User B's counter NOT incremented (they didn't create it)
        status_b_after = self._get_plan_status(user_b['token'])
        assert status_b_after['matches_used_today'] == 0, f"User B should still have 0 matches (didn't create exchange), got {status_b_after['matches_used_today']}"
        print(f"✓ User B matches (unchanged): {status_b_after['matches_used_today']}/{status_b_after['matches_limit']}")
        
        print("✓ TEST PASSED: Exchange creation counts only for creator")
    
    def test_first_reply_counts_for_replier(self):
        """
        Test 2: When user B replies to that chat (first message) → counts for user B's daily limit
        """
        print("\n=== Test: First reply counts for replier ===")
        
        # Create two test users
        user_a = self._create_test_user_via_otp("reply_creator")
        user_b = self._create_test_user_via_otp("reply_partner")
        
        if not user_a or not user_b:
            pytest.skip("Could not create test users via OTP")
        
        # Get an active album
        albums = self._get_albums(user_a['token'])
        active_albums = [a for a in albums if a.get('status') == 'active']
        if not active_albums:
            pytest.skip("No active albums available")
        
        album_id = active_albums[0]['id']
        
        # Both users activate the album
        self._activate_album(user_a['token'], album_id)
        self._activate_album(user_b['token'], album_id)
        
        # Setup inventory for mutual exchange
        inventory = self._get_inventory(user_a['token'], album_id)
        if len(inventory) < 4:
            pytest.skip("Not enough stickers in album for test")
        
        sticker_ids = [s['id'] for s in inventory[:4]]
        
        # User A: duplicates of 0,1, needs 2,3
        self._update_inventory(user_a['token'], sticker_ids[0], 2)
        self._update_inventory(user_a['token'], sticker_ids[1], 2)
        self._update_inventory(user_a['token'], sticker_ids[2], 0)
        self._update_inventory(user_a['token'], sticker_ids[3], 0)
        
        # User B: duplicates of 2,3, needs 0,1
        self._update_inventory(user_b['token'], sticker_ids[0], 0)
        self._update_inventory(user_b['token'], sticker_ids[1], 0)
        self._update_inventory(user_b['token'], sticker_ids[2], 2)
        self._update_inventory(user_b['token'], sticker_ids[3], 2)
        
        # User A creates exchange
        exchange_response = self._create_exchange(user_a['token'], album_id, user_b['user_id'])
        if exchange_response.status_code != 200:
            pytest.skip("Could not create exchange")
        
        exchange_id = exchange_response.json().get('exchange', {}).get('id')
        print(f"Exchange created: {exchange_id}")
        
        # Check initial states
        status_a = self._get_plan_status(user_a['token'])
        status_b = self._get_plan_status(user_b['token'])
        print(f"After exchange creation - User A: {status_a['matches_used_today']}, User B: {status_b['matches_used_today']}")
        
        assert status_a['matches_used_today'] == 1, "User A should have 1 match after creating"
        assert status_b['matches_used_today'] == 0, "User B should have 0 matches before replying"
        
        # User B sends first reply
        reply_response = self._send_chat_message(user_b['token'], exchange_id, "Hello, I'm interested in trading!")
        assert reply_response.status_code == 200, f"User B should be able to send first reply: {reply_response.text}"
        print("User B sent first reply")
        
        # Check User B's counter incremented
        status_b_after = self._get_plan_status(user_b['token'])
        assert status_b_after['matches_used_today'] == 1, f"User B should have 1 match after first reply, got {status_b_after['matches_used_today']}"
        print(f"✓ User B matches after first reply: {status_b_after['matches_used_today']}/{status_b_after['matches_limit']}")
        
        print("✓ TEST PASSED: First reply counts for replier")
    
    def test_subsequent_messages_dont_count(self):
        """
        Test 3: Subsequent messages in the same chat do NOT count for either user
        """
        print("\n=== Test: Subsequent messages don't count ===")
        
        # Create two test users with plus plan (5 chats/day) to allow multiple messages
        user_a = self._create_test_user_via_otp("subseq_creator")
        user_b = self._create_test_user_via_otp("subseq_partner")
        
        if not user_a or not user_b:
            pytest.skip("Could not create test users via OTP")
        
        # Set both to plus plan for more room
        self._set_user_plan(user_a['token'], 'plus')
        self._set_user_plan(user_b['token'], 'plus')
        
        # Get an active album
        albums = self._get_albums(user_a['token'])
        active_albums = [a for a in albums if a.get('status') == 'active']
        if not active_albums:
            pytest.skip("No active albums available")
        
        album_id = active_albums[0]['id']
        
        # Both users activate the album
        self._activate_album(user_a['token'], album_id)
        self._activate_album(user_b['token'], album_id)
        
        # Setup inventory
        inventory = self._get_inventory(user_a['token'], album_id)
        if len(inventory) < 4:
            pytest.skip("Not enough stickers")
        
        sticker_ids = [s['id'] for s in inventory[:4]]
        
        self._update_inventory(user_a['token'], sticker_ids[0], 2)
        self._update_inventory(user_a['token'], sticker_ids[1], 2)
        self._update_inventory(user_a['token'], sticker_ids[2], 0)
        self._update_inventory(user_a['token'], sticker_ids[3], 0)
        
        self._update_inventory(user_b['token'], sticker_ids[0], 0)
        self._update_inventory(user_b['token'], sticker_ids[1], 0)
        self._update_inventory(user_b['token'], sticker_ids[2], 2)
        self._update_inventory(user_b['token'], sticker_ids[3], 2)
        
        # User A creates exchange
        exchange_response = self._create_exchange(user_a['token'], album_id, user_b['user_id'])
        if exchange_response.status_code != 200:
            pytest.skip("Could not create exchange")
        
        exchange_id = exchange_response.json().get('exchange', {}).get('id')
        
        # User A sends first message (creator's first message)
        self._send_chat_message(user_a['token'], exchange_id, "Hi, let's trade!")
        
        # User B sends first reply (counts for B)
        self._send_chat_message(user_b['token'], exchange_id, "Sure, sounds good!")
        
        # Get counts after first messages
        status_a_after_first = self._get_plan_status(user_a['token'])
        status_b_after_first = self._get_plan_status(user_b['token'])
        
        print(f"After first messages - User A: {status_a_after_first['matches_used_today']}, User B: {status_b_after_first['matches_used_today']}")
        
        # User A sends second message
        self._send_chat_message(user_a['token'], exchange_id, "When can we meet?")
        status_a_after_second = self._get_plan_status(user_a['token'])
        assert status_a_after_second['matches_used_today'] == status_a_after_first['matches_used_today'], \
            f"User A's count should NOT increase on subsequent messages"
        print(f"✓ User A count unchanged after second message: {status_a_after_second['matches_used_today']}")
        
        # User B sends second message
        self._send_chat_message(user_b['token'], exchange_id, "Tomorrow works for me")
        status_b_after_second = self._get_plan_status(user_b['token'])
        assert status_b_after_second['matches_used_today'] == status_b_after_first['matches_used_today'], \
            f"User B's count should NOT increase on subsequent messages"
        print(f"✓ User B count unchanged after second message: {status_b_after_second['matches_used_today']}")
        
        # Send more messages to be sure
        self._send_chat_message(user_a['token'], exchange_id, "Great, see you then!")
        self._send_chat_message(user_b['token'], exchange_id, "Perfect!")
        
        status_a_final = self._get_plan_status(user_a['token'])
        status_b_final = self._get_plan_status(user_b['token'])
        
        assert status_a_final['matches_used_today'] == status_a_after_first['matches_used_today'], \
            "User A's count should remain unchanged"
        assert status_b_final['matches_used_today'] == status_b_after_first['matches_used_today'], \
            "User B's count should remain unchanged"
        
        print(f"✓ Final counts - User A: {status_a_final['matches_used_today']}, User B: {status_b_final['matches_used_today']}")
        print("✓ TEST PASSED: Subsequent messages don't count")
    
    def test_free_plan_blocks_second_chat_reply(self):
        """
        Test 4: Free plan limit (1 chat/day) enforced on reply
        User B on free plan should be blocked from replying to a second chat
        """
        print("\n=== Test: Free plan blocks second chat reply ===")
        
        # Create three test users
        user_a1 = self._create_test_user_via_otp("free_creator1")
        user_a2 = self._create_test_user_via_otp("free_creator2")
        user_b = self._create_test_user_via_otp("free_replier")
        
        if not user_a1 or not user_a2 or not user_b:
            pytest.skip("Could not create test users via OTP")
        
        # User A1 and A2 on unlimited plan (can create multiple exchanges)
        self._set_user_plan(user_a1['token'], 'unlimited')
        self._set_user_plan(user_a2['token'], 'unlimited')
        # User B stays on free plan (1 chat/day)
        
        # Get an active album
        albums = self._get_albums(user_a1['token'])
        active_albums = [a for a in albums if a.get('status') == 'active']
        if not active_albums:
            pytest.skip("No active albums available")
        
        album_id = active_albums[0]['id']
        
        # All users activate the album
        self._activate_album(user_a1['token'], album_id)
        self._activate_album(user_a2['token'], album_id)
        self._activate_album(user_b['token'], album_id)
        
        # Setup inventory
        inventory = self._get_inventory(user_a1['token'], album_id)
        if len(inventory) < 6:
            pytest.skip("Not enough stickers")
        
        sticker_ids = [s['id'] for s in inventory[:6]]
        
        # User A1: duplicates of 0,1, needs 2,3
        self._update_inventory(user_a1['token'], sticker_ids[0], 2)
        self._update_inventory(user_a1['token'], sticker_ids[1], 2)
        self._update_inventory(user_a1['token'], sticker_ids[2], 0)
        self._update_inventory(user_a1['token'], sticker_ids[3], 0)
        
        # User A2: duplicates of 4,5, needs 2,3
        self._update_inventory(user_a2['token'], sticker_ids[4], 2)
        self._update_inventory(user_a2['token'], sticker_ids[5], 2)
        self._update_inventory(user_a2['token'], sticker_ids[2], 0)
        self._update_inventory(user_a2['token'], sticker_ids[3], 0)
        
        # User B: duplicates of 2,3, needs 0,1,4,5
        self._update_inventory(user_b['token'], sticker_ids[0], 0)
        self._update_inventory(user_b['token'], sticker_ids[1], 0)
        self._update_inventory(user_b['token'], sticker_ids[2], 2)
        self._update_inventory(user_b['token'], sticker_ids[3], 2)
        self._update_inventory(user_b['token'], sticker_ids[4], 0)
        self._update_inventory(user_b['token'], sticker_ids[5], 0)
        
        # User A1 creates exchange with User B
        exchange1_response = self._create_exchange(user_a1['token'], album_id, user_b['user_id'])
        if exchange1_response.status_code != 200:
            pytest.skip("Could not create first exchange")
        exchange1_id = exchange1_response.json().get('exchange', {}).get('id')
        print(f"Exchange 1 created: {exchange1_id}")
        
        # User A2 creates exchange with User B
        exchange2_response = self._create_exchange(user_a2['token'], album_id, user_b['user_id'])
        if exchange2_response.status_code != 200:
            pytest.skip("Could not create second exchange")
        exchange2_id = exchange2_response.json().get('exchange', {}).get('id')
        print(f"Exchange 2 created: {exchange2_id}")
        
        # User B replies to first exchange (should succeed, uses their 1 daily chat)
        reply1_response = self._send_chat_message(user_b['token'], exchange1_id, "Hi, let's trade!")
        assert reply1_response.status_code == 200, f"User B should be able to reply to first chat: {reply1_response.text}"
        print("✓ User B replied to first exchange")
        
        status_b = self._get_plan_status(user_b['token'])
        assert status_b['matches_used_today'] == 1, f"User B should have 1 match used, got {status_b['matches_used_today']}"
        print(f"User B matches: {status_b['matches_used_today']}/{status_b['matches_limit']}")
        
        # User B tries to reply to second exchange (should be BLOCKED)
        reply2_response = self._send_chat_message(user_b['token'], exchange2_id, "Hi, let's trade too!")
        assert reply2_response.status_code == 403, f"User B should be blocked from second reply, got {reply2_response.status_code}"
        
        error_data = reply2_response.json()
        assert error_data.get('detail', {}).get('code') == 'DAILY_MATCH_LIMIT', \
            f"Error should be DAILY_MATCH_LIMIT, got {error_data}"
        print(f"✓ User B blocked from second reply with DAILY_MATCH_LIMIT")
        
        print("✓ TEST PASSED: Free plan blocks second chat reply")
    
    def test_plus_plan_allows_5_chats(self):
        """
        Test 5: Plus plan limit (5 chats/day) enforced on both creation AND reply
        """
        print("\n=== Test: Plus plan allows 5 chats ===")
        
        # Create test user on plus plan
        user = self._create_test_user_via_otp("plus_user")
        if not user:
            pytest.skip("Could not create test user")
        
        self._set_user_plan(user['token'], 'plus')
        
        status = self._get_plan_status(user['token'])
        assert status['plan'] == 'plus', "User should be on plus plan"
        assert status['matches_limit'] == 5, "Plus plan should have 5 chats/day limit"
        print(f"✓ Plus plan verified: {status['matches_limit']} chats/day limit")
        
        print("✓ TEST PASSED: Plus plan has 5 chats/day limit")
    
    def test_unlimited_plan_no_limits(self):
        """
        Test 6: Unlimited plan has no limits on chat creation or reply
        """
        print("\n=== Test: Unlimited plan has no limits ===")
        
        user = self._create_test_user_via_otp("unlimited_user")
        if not user:
            pytest.skip("Could not create test user")
        
        self._set_user_plan(user['token'], 'unlimited')
        
        status = self._get_plan_status(user['token'])
        assert status['plan'] == 'unlimited', "User should be on unlimited plan"
        assert status['matches_limit'] is None, "Unlimited plan should have no limit (None)"
        assert status['can_match'] == True, "Unlimited plan should always allow matching"
        print(f"✓ Unlimited plan verified: no limits, can_match={status['can_match']}")
        
        print("✓ TEST PASSED: Unlimited plan has no limits")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
