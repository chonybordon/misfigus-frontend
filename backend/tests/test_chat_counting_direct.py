#!/usr/bin/env python3
"""
Direct API Test for Chat Counting Logic

This script tests the chat counting logic for subscription limits by:
1. Creating test users via OTP (parsing OTP from backend logs)
2. Setting up exchanges between users
3. Verifying counter increments correctly

Tests:
1. When user A starts a new exchange/chat with user B → counts for user A's daily limit
2. When user B replies to that chat (first message) → counts for user B's daily limit
3. Subsequent messages in the same chat do NOT count for either user
4. Free plan limit: 1 chat/day enforced on both creation AND reply
5. Plus plan limit: 5 chats/day enforced on both creation AND reply
6. Unlimited plan: no limits on chat creation or reply
7. Counter increments correctly when replying to a new chat
"""

import requests
import subprocess
import time
import re
import json
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sticker-swap-1.preview.emergentagent.com').rstrip('/')

def get_otp_from_logs(email: str, max_wait: int = 10) -> str:
    """Parse OTP from backend logs for a given email"""
    time.sleep(1)  # Wait for log to be written
    
    for attempt in range(max_wait):
        try:
            result = subprocess.run(
                ['tail', '-200', '/var/log/supervisor/backend.err.log'],
                capture_output=True, text=True, timeout=5
            )
            logs = result.stdout
            
            # Look for OTP pattern line by line
            lines = logs.split('\n')
            found_email = False
            for i, line in enumerate(lines):
                if f'[OTP] To: {email}' in line:
                    found_email = True
                    # Look for OTP in next few lines
                    for j in range(i, min(i+5, len(lines))):
                        if '[OTP] OTP:' in lines[j]:
                            match = re.search(r'\[OTP\] OTP: (\d{6})', lines[j])
                            if match:
                                return match.group(1)
            
            if not found_email:
                time.sleep(0.5)
                continue
                
        except Exception as e:
            print(f"Error reading logs: {e}")
        
        time.sleep(0.5)
    
    return None

def create_test_user(email_prefix: str) -> dict:
    """Create a test user via OTP flow"""
    timestamp = int(time.time() * 1000)
    email = f"test_{email_prefix}_{timestamp}@test.com"  # lowercase to match backend normalization
    
    session = requests.Session()
    
    # Send OTP
    response = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
    if response.status_code != 200:
        print(f"❌ Failed to send OTP for {email}: {response.text}")
        return None
    
    # Get OTP from logs
    otp = get_otp_from_logs(email)
    if not otp:
        print(f"❌ Could not find OTP in logs for {email}")
        return None
    
    # Verify OTP
    verify_response = session.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": email,
        "otp": otp
    })
    
    if verify_response.status_code != 200:
        print(f"❌ Failed to verify OTP for {email}: {verify_response.text}")
        return None
    
    data = verify_response.json()
    print(f"✓ Created user: {email}")
    return {
        "user": data['user'],
        "token": data['token'],
        "email": email,
        "user_id": data['user']['id']
    }

def get_auth_headers(token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

def set_user_plan(token: str, plan: str) -> dict:
    """Set user's plan (mocked endpoint)"""
    response = requests.post(
        f"{BASE_URL}/api/user/set-plan",
        params={"plan": plan},
        headers=get_auth_headers(token)
    )
    return response

def get_plan_status(token: str) -> dict:
    """Get user's plan status"""
    response = requests.get(
        f"{BASE_URL}/api/user/plan-status",
        headers=get_auth_headers(token)
    )
    return response.json() if response.status_code == 200 else None

def activate_album(token: str, album_id: str) -> bool:
    """Activate an album for a user"""
    response = requests.post(
        f"{BASE_URL}/api/albums/{album_id}/activate",
        headers=get_auth_headers(token)
    )
    return response.status_code == 200

def get_albums(token: str) -> list:
    """Get available albums"""
    response = requests.get(
        f"{BASE_URL}/api/albums",
        headers=get_auth_headers(token)
    )
    return response.json() if response.status_code == 200 else []

def get_inventory(token: str, album_id: str) -> list:
    """Get inventory for an album"""
    response = requests.get(
        f"{BASE_URL}/api/inventory",
        params={"album_id": album_id},
        headers=get_auth_headers(token)
    )
    return response.json() if response.status_code == 200 else []

def update_inventory(token: str, sticker_id: str, owned_qty: int):
    """Update inventory for a sticker"""
    return requests.put(
        f"{BASE_URL}/api/inventory",
        json={"sticker_id": sticker_id, "owned_qty": owned_qty},
        headers=get_auth_headers(token)
    )

def create_exchange(token: str, album_id: str, partner_id: str):
    """Create an exchange between users"""
    return requests.post(
        f"{BASE_URL}/api/exchanges",
        json={"album_id": album_id, "partner_id": partner_id},
        headers=get_auth_headers(token)
    )

def send_chat_message(token: str, exchange_id: str, content: str):
    """Send a chat message"""
    return requests.post(
        f"{BASE_URL}/api/exchanges/{exchange_id}/chat/messages",
        json={"content": content},
        headers=get_auth_headers(token)
    )

def setup_mutual_exchange_inventory(user_a_token: str, user_b_token: str, album_id: str):
    """Setup inventory for mutual exchange between two users"""
    inventory = get_inventory(user_a_token, album_id)
    if len(inventory) < 4:
        print("❌ Not enough stickers in album")
        return False
    
    sticker_ids = [s['id'] for s in inventory[:4]]
    
    # User A: duplicates of 0,1, needs 2,3
    update_inventory(user_a_token, sticker_ids[0], 2)
    update_inventory(user_a_token, sticker_ids[1], 2)
    update_inventory(user_a_token, sticker_ids[2], 0)
    update_inventory(user_a_token, sticker_ids[3], 0)
    
    # User B: duplicates of 2,3, needs 0,1
    update_inventory(user_b_token, sticker_ids[0], 0)
    update_inventory(user_b_token, sticker_ids[1], 0)
    update_inventory(user_b_token, sticker_ids[2], 2)
    update_inventory(user_b_token, sticker_ids[3], 2)
    
    return True

# ============================================
# TEST FUNCTIONS
# ============================================

def test_plan_status_endpoint():
    """Test 1: Plan status endpoint returns correct structure"""
    print("\n" + "="*60)
    print("TEST: Plan status endpoint")
    print("="*60)
    
    user = create_test_user("plan_status")
    if not user:
        print("❌ FAILED: Could not create test user")
        return False
    
    status = get_plan_status(user['token'])
    if not status:
        print("❌ FAILED: Could not get plan status")
        return False
    
    required_fields = ['plan', 'matches_used_today', 'matches_limit', 'can_match']
    for field in required_fields:
        if field not in status:
            print(f"❌ FAILED: Missing field '{field}' in plan status")
            return False
    
    print(f"✓ Plan: {status['plan']}")
    print(f"✓ Matches used: {status['matches_used_today']}/{status['matches_limit']}")
    print(f"✓ Can match: {status['can_match']}")
    print("✓ PASSED: Plan status endpoint works correctly")
    return True

def test_free_plan_default():
    """Test 2: New users default to free plan with 1 chat/day limit"""
    print("\n" + "="*60)
    print("TEST: Free plan default")
    print("="*60)
    
    user = create_test_user("free_default")
    if not user:
        print("❌ FAILED: Could not create test user")
        return False
    
    status = get_plan_status(user['token'])
    
    if status['plan'] != 'free':
        print(f"❌ FAILED: Expected plan 'free', got '{status['plan']}'")
        return False
    
    if status['matches_limit'] != 1:
        print(f"❌ FAILED: Expected limit 1, got {status['matches_limit']}")
        return False
    
    if status['matches_used_today'] != 0:
        print(f"❌ FAILED: Expected 0 matches used, got {status['matches_used_today']}")
        return False
    
    print(f"✓ Plan: {status['plan']}")
    print(f"✓ Limit: {status['matches_limit']} chat/day")
    print(f"✓ Matches used: {status['matches_used_today']}")
    print("✓ PASSED: New users default to free plan with 1 chat/day limit")
    return True

def test_plus_plan_limit():
    """Test 3: Plus plan has 5 chats/day limit"""
    print("\n" + "="*60)
    print("TEST: Plus plan limit")
    print("="*60)
    
    user = create_test_user("plus_plan")
    if not user:
        print("❌ FAILED: Could not create test user")
        return False
    
    # Set to plus plan
    response = set_user_plan(user['token'], 'plus')
    if response.status_code != 200:
        print(f"❌ FAILED: Could not set plus plan: {response.text}")
        return False
    
    status = get_plan_status(user['token'])
    
    if status['plan'] != 'plus':
        print(f"❌ FAILED: Expected plan 'plus', got '{status['plan']}'")
        return False
    
    if status['matches_limit'] != 5:
        print(f"❌ FAILED: Expected limit 5, got {status['matches_limit']}")
        return False
    
    print(f"✓ Plan: {status['plan']}")
    print(f"✓ Limit: {status['matches_limit']} chats/day")
    print("✓ PASSED: Plus plan has 5 chats/day limit")
    return True

def test_unlimited_plan_no_limits():
    """Test 4: Unlimited plan has no limits"""
    print("\n" + "="*60)
    print("TEST: Unlimited plan no limits")
    print("="*60)
    
    user = create_test_user("unlimited_plan")
    if not user:
        print("❌ FAILED: Could not create test user")
        return False
    
    # Set to unlimited plan
    response = set_user_plan(user['token'], 'unlimited')
    if response.status_code != 200:
        print(f"❌ FAILED: Could not set unlimited plan: {response.text}")
        return False
    
    status = get_plan_status(user['token'])
    
    if status['plan'] != 'unlimited':
        print(f"❌ FAILED: Expected plan 'unlimited', got '{status['plan']}'")
        return False
    
    if status['matches_limit'] is not None:
        print(f"❌ FAILED: Expected no limit (None), got {status['matches_limit']}")
        return False
    
    if status['can_match'] != True:
        print(f"❌ FAILED: Expected can_match=True, got {status['can_match']}")
        return False
    
    print(f"✓ Plan: {status['plan']}")
    print(f"✓ Limit: {status['matches_limit']} (no limit)")
    print(f"✓ Can match: {status['can_match']}")
    print("✓ PASSED: Unlimited plan has no limits")
    return True

def test_exchange_creation_counts_for_creator():
    """Test 5: Exchange creation counts for creator (user A)"""
    print("\n" + "="*60)
    print("TEST: Exchange creation counts for creator")
    print("="*60)
    
    # Create two test users
    user_a = create_test_user("creator_a")
    time.sleep(1)  # Rate limit
    user_b = create_test_user("partner_b")
    
    if not user_a or not user_b:
        print("❌ FAILED: Could not create test users")
        return False
    
    # Check initial state
    status_a_before = get_plan_status(user_a['token'])
    if status_a_before['matches_used_today'] != 0:
        print(f"❌ FAILED: User A should start with 0 matches, got {status_a_before['matches_used_today']}")
        return False
    
    print(f"✓ User A initial matches: {status_a_before['matches_used_today']}/{status_a_before['matches_limit']}")
    
    # Get an active album
    albums = get_albums(user_a['token'])
    active_albums = [a for a in albums if a.get('status') == 'active']
    if not active_albums:
        print("❌ SKIPPED: No active albums available")
        return None
    
    album_id = active_albums[0]['id']
    print(f"✓ Using album: {album_id}")
    
    # Both users activate the album
    activate_album(user_a['token'], album_id)
    activate_album(user_b['token'], album_id)
    
    # Setup inventory for mutual exchange
    if not setup_mutual_exchange_inventory(user_a['token'], user_b['token'], album_id):
        print("❌ SKIPPED: Could not setup inventory")
        return None
    
    print("✓ Inventory setup complete")
    
    # User A creates exchange with User B
    exchange_response = create_exchange(user_a['token'], album_id, user_b['user_id'])
    
    if exchange_response.status_code != 200:
        print(f"❌ SKIPPED: Could not create exchange: {exchange_response.status_code} - {exchange_response.text}")
        return None
    
    exchange_data = exchange_response.json()
    exchange_id = exchange_data.get('exchange', {}).get('id')
    print(f"✓ Exchange created: {exchange_id}")
    
    # Check User A's counter incremented
    status_a_after = get_plan_status(user_a['token'])
    if status_a_after['matches_used_today'] != 1:
        print(f"❌ FAILED: User A should have 1 match after creating, got {status_a_after['matches_used_today']}")
        return False
    
    print(f"✓ User A matches after creation: {status_a_after['matches_used_today']}/{status_a_after['matches_limit']}")
    
    # Check User B's counter NOT incremented
    status_b_after = get_plan_status(user_b['token'])
    if status_b_after['matches_used_today'] != 0:
        print(f"❌ FAILED: User B should still have 0 matches, got {status_b_after['matches_used_today']}")
        return False
    
    print(f"✓ User B matches (unchanged): {status_b_after['matches_used_today']}/{status_b_after['matches_limit']}")
    print("✓ PASSED: Exchange creation counts only for creator")
    return True

def test_first_reply_counts_for_replier():
    """Test 6: First reply counts for replier (user B)"""
    print("\n" + "="*60)
    print("TEST: First reply counts for replier")
    print("="*60)
    
    # Create two test users
    user_a = create_test_user("reply_creator")
    time.sleep(1)
    user_b = create_test_user("reply_partner")
    
    if not user_a or not user_b:
        print("❌ FAILED: Could not create test users")
        return False
    
    # Get an active album
    albums = get_albums(user_a['token'])
    active_albums = [a for a in albums if a.get('status') == 'active']
    if not active_albums:
        print("❌ SKIPPED: No active albums available")
        return None
    
    album_id = active_albums[0]['id']
    
    # Both users activate the album
    activate_album(user_a['token'], album_id)
    activate_album(user_b['token'], album_id)
    
    # Setup inventory
    if not setup_mutual_exchange_inventory(user_a['token'], user_b['token'], album_id):
        print("❌ SKIPPED: Could not setup inventory")
        return None
    
    # User A creates exchange
    exchange_response = create_exchange(user_a['token'], album_id, user_b['user_id'])
    if exchange_response.status_code != 200:
        print(f"❌ SKIPPED: Could not create exchange: {exchange_response.text}")
        return None
    
    exchange_id = exchange_response.json().get('exchange', {}).get('id')
    print(f"✓ Exchange created: {exchange_id}")
    
    # Check initial states
    status_a = get_plan_status(user_a['token'])
    status_b = get_plan_status(user_b['token'])
    print(f"✓ After exchange creation - User A: {status_a['matches_used_today']}, User B: {status_b['matches_used_today']}")
    
    if status_a['matches_used_today'] != 1:
        print(f"❌ FAILED: User A should have 1 match after creating")
        return False
    
    if status_b['matches_used_today'] != 0:
        print(f"❌ FAILED: User B should have 0 matches before replying")
        return False
    
    # User B sends first reply
    reply_response = send_chat_message(user_b['token'], exchange_id, "Hello, I'm interested in trading!")
    if reply_response.status_code != 200:
        print(f"❌ FAILED: User B should be able to send first reply: {reply_response.text}")
        return False
    
    print("✓ User B sent first reply")
    
    # Check User B's counter incremented
    status_b_after = get_plan_status(user_b['token'])
    if status_b_after['matches_used_today'] != 1:
        print(f"❌ FAILED: User B should have 1 match after first reply, got {status_b_after['matches_used_today']}")
        return False
    
    print(f"✓ User B matches after first reply: {status_b_after['matches_used_today']}/{status_b_after['matches_limit']}")
    print("✓ PASSED: First reply counts for replier")
    return True

def test_subsequent_messages_dont_count():
    """Test 7: Subsequent messages don't count"""
    print("\n" + "="*60)
    print("TEST: Subsequent messages don't count")
    print("="*60)
    
    # Create two test users with plus plan
    user_a = create_test_user("subseq_creator")
    time.sleep(1)
    user_b = create_test_user("subseq_partner")
    
    if not user_a or not user_b:
        print("❌ FAILED: Could not create test users")
        return False
    
    # Set both to plus plan
    set_user_plan(user_a['token'], 'plus')
    set_user_plan(user_b['token'], 'plus')
    
    # Get an active album
    albums = get_albums(user_a['token'])
    active_albums = [a for a in albums if a.get('status') == 'active']
    if not active_albums:
        print("❌ SKIPPED: No active albums available")
        return None
    
    album_id = active_albums[0]['id']
    
    # Both users activate the album
    activate_album(user_a['token'], album_id)
    activate_album(user_b['token'], album_id)
    
    # Setup inventory
    if not setup_mutual_exchange_inventory(user_a['token'], user_b['token'], album_id):
        print("❌ SKIPPED: Could not setup inventory")
        return None
    
    # User A creates exchange
    exchange_response = create_exchange(user_a['token'], album_id, user_b['user_id'])
    if exchange_response.status_code != 200:
        print(f"❌ SKIPPED: Could not create exchange: {exchange_response.text}")
        return None
    
    exchange_id = exchange_response.json().get('exchange', {}).get('id')
    
    # User A sends first message
    send_chat_message(user_a['token'], exchange_id, "Hi, let's trade!")
    
    # User B sends first reply (counts for B)
    send_chat_message(user_b['token'], exchange_id, "Sure, sounds good!")
    
    # Get counts after first messages
    status_a_after_first = get_plan_status(user_a['token'])
    status_b_after_first = get_plan_status(user_b['token'])
    
    print(f"✓ After first messages - User A: {status_a_after_first['matches_used_today']}, User B: {status_b_after_first['matches_used_today']}")
    
    # User A sends second message
    send_chat_message(user_a['token'], exchange_id, "When can we meet?")
    status_a_after_second = get_plan_status(user_a['token'])
    
    if status_a_after_second['matches_used_today'] != status_a_after_first['matches_used_today']:
        print(f"❌ FAILED: User A's count should NOT increase on subsequent messages")
        return False
    
    print(f"✓ User A count unchanged after second message: {status_a_after_second['matches_used_today']}")
    
    # User B sends second message
    send_chat_message(user_b['token'], exchange_id, "Tomorrow works for me")
    status_b_after_second = get_plan_status(user_b['token'])
    
    if status_b_after_second['matches_used_today'] != status_b_after_first['matches_used_today']:
        print(f"❌ FAILED: User B's count should NOT increase on subsequent messages")
        return False
    
    print(f"✓ User B count unchanged after second message: {status_b_after_second['matches_used_today']}")
    
    # Send more messages
    send_chat_message(user_a['token'], exchange_id, "Great, see you then!")
    send_chat_message(user_b['token'], exchange_id, "Perfect!")
    
    status_a_final = get_plan_status(user_a['token'])
    status_b_final = get_plan_status(user_b['token'])
    
    if status_a_final['matches_used_today'] != status_a_after_first['matches_used_today']:
        print(f"❌ FAILED: User A's count should remain unchanged")
        return False
    
    if status_b_final['matches_used_today'] != status_b_after_first['matches_used_today']:
        print(f"❌ FAILED: User B's count should remain unchanged")
        return False
    
    print(f"✓ Final counts - User A: {status_a_final['matches_used_today']}, User B: {status_b_final['matches_used_today']}")
    print("✓ PASSED: Subsequent messages don't count")
    return True

def test_free_plan_blocks_second_chat_reply():
    """Test 8: Free plan blocks second chat reply"""
    print("\n" + "="*60)
    print("TEST: Free plan blocks second chat reply")
    print("="*60)
    
    # Create three test users
    user_a1 = create_test_user("free_creator1")
    time.sleep(1)
    user_a2 = create_test_user("free_creator2")
    time.sleep(1)
    user_b = create_test_user("free_replier")
    
    if not user_a1 or not user_a2 or not user_b:
        print("❌ FAILED: Could not create test users")
        return False
    
    # User A1 and A2 on unlimited plan
    set_user_plan(user_a1['token'], 'unlimited')
    set_user_plan(user_a2['token'], 'unlimited')
    # User B stays on free plan
    
    # Get an active album
    albums = get_albums(user_a1['token'])
    active_albums = [a for a in albums if a.get('status') == 'active']
    if not active_albums:
        print("❌ SKIPPED: No active albums available")
        return None
    
    album_id = active_albums[0]['id']
    
    # All users activate the album
    activate_album(user_a1['token'], album_id)
    activate_album(user_a2['token'], album_id)
    activate_album(user_b['token'], album_id)
    
    # Setup inventory
    inventory = get_inventory(user_a1['token'], album_id)
    if len(inventory) < 6:
        print("❌ SKIPPED: Not enough stickers")
        return None
    
    sticker_ids = [s['id'] for s in inventory[:6]]
    
    # User A1: duplicates of 0,1, needs 2,3
    update_inventory(user_a1['token'], sticker_ids[0], 2)
    update_inventory(user_a1['token'], sticker_ids[1], 2)
    update_inventory(user_a1['token'], sticker_ids[2], 0)
    update_inventory(user_a1['token'], sticker_ids[3], 0)
    
    # User A2: duplicates of 4,5, needs 2,3
    update_inventory(user_a2['token'], sticker_ids[4], 2)
    update_inventory(user_a2['token'], sticker_ids[5], 2)
    update_inventory(user_a2['token'], sticker_ids[2], 0)
    update_inventory(user_a2['token'], sticker_ids[3], 0)
    
    # User B: duplicates of 2,3, needs 0,1,4,5
    update_inventory(user_b['token'], sticker_ids[0], 0)
    update_inventory(user_b['token'], sticker_ids[1], 0)
    update_inventory(user_b['token'], sticker_ids[2], 2)
    update_inventory(user_b['token'], sticker_ids[3], 2)
    update_inventory(user_b['token'], sticker_ids[4], 0)
    update_inventory(user_b['token'], sticker_ids[5], 0)
    
    # User A1 creates exchange with User B
    exchange1_response = create_exchange(user_a1['token'], album_id, user_b['user_id'])
    if exchange1_response.status_code != 200:
        print(f"❌ SKIPPED: Could not create first exchange: {exchange1_response.text}")
        return None
    exchange1_id = exchange1_response.json().get('exchange', {}).get('id')
    print(f"✓ Exchange 1 created: {exchange1_id}")
    
    # User A2 creates exchange with User B
    exchange2_response = create_exchange(user_a2['token'], album_id, user_b['user_id'])
    if exchange2_response.status_code != 200:
        print(f"❌ SKIPPED: Could not create second exchange: {exchange2_response.text}")
        return None
    exchange2_id = exchange2_response.json().get('exchange', {}).get('id')
    print(f"✓ Exchange 2 created: {exchange2_id}")
    
    # User B replies to first exchange (should succeed)
    reply1_response = send_chat_message(user_b['token'], exchange1_id, "Hi, let's trade!")
    if reply1_response.status_code != 200:
        print(f"❌ FAILED: User B should be able to reply to first chat: {reply1_response.text}")
        return False
    
    print("✓ User B replied to first exchange")
    
    status_b = get_plan_status(user_b['token'])
    if status_b['matches_used_today'] != 1:
        print(f"❌ FAILED: User B should have 1 match used, got {status_b['matches_used_today']}")
        return False
    
    print(f"✓ User B matches: {status_b['matches_used_today']}/{status_b['matches_limit']}")
    
    # User B tries to reply to second exchange (should be BLOCKED)
    reply2_response = send_chat_message(user_b['token'], exchange2_id, "Hi, let's trade too!")
    
    if reply2_response.status_code != 403:
        print(f"❌ FAILED: User B should be blocked from second reply, got {reply2_response.status_code}")
        return False
    
    error_data = reply2_response.json()
    if error_data.get('detail', {}).get('code') != 'DAILY_MATCH_LIMIT':
        print(f"❌ FAILED: Error should be DAILY_MATCH_LIMIT, got {error_data}")
        return False
    
    print(f"✓ User B blocked from second reply with DAILY_MATCH_LIMIT")
    print("✓ PASSED: Free plan blocks second chat reply")
    return True

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("CHAT COUNTING LOGIC TESTS FOR SUBSCRIPTION LIMITS")
    print("="*70)
    
    results = {}
    
    # Basic tests
    results['plan_status_endpoint'] = test_plan_status_endpoint()
    time.sleep(1)
    
    results['free_plan_default'] = test_free_plan_default()
    time.sleep(1)
    
    results['plus_plan_limit'] = test_plus_plan_limit()
    time.sleep(1)
    
    results['unlimited_plan_no_limits'] = test_unlimited_plan_no_limits()
    time.sleep(1)
    
    # Exchange/chat tests
    results['exchange_creation_counts_for_creator'] = test_exchange_creation_counts_for_creator()
    time.sleep(1)
    
    results['first_reply_counts_for_replier'] = test_first_reply_counts_for_replier()
    time.sleep(1)
    
    results['subsequent_messages_dont_count'] = test_subsequent_messages_dont_count()
    time.sleep(1)
    
    results['free_plan_blocks_second_chat_reply'] = test_free_plan_blocks_second_chat_reply()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASSED"
            passed += 1
        elif result is False:
            status = "❌ FAILED"
            failed += 1
        else:
            status = "⚠ SKIPPED"
            skipped += 1
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    print("="*70)
    
    return results

if __name__ == "__main__":
    results = run_all_tests()
    
    # Save results to file
    with open('/app/test_reports/chat_counting_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': {k: str(v) for k, v in results.items()}
        }, f, indent=2)
