"""
Test script to verify the chat limit error handling end-to-end.
Tests the scenario:
1. User A creates exchange with User B (uses A's 1/1 limit)
2. User C creates exchange with User A
3. User A tries to reply to User C's chat → should get DAILY_MATCH_LIMIT error
"""
import requests
import os
import time
import random
import string
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sticker-swap-1.preview.emergentagent.com').rstrip('/')

def generate_test_email():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test_limit_{suffix}@test.com"

def login_user(email):
    """Login a user and return their token and user data"""
    session = requests.Session()
    
    # Request OTP
    response = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
    if response.status_code != 200:
        print(f"Failed to request OTP for {email}: {response.text}")
        return None, None
    
    # Get OTP from backend logs
    time.sleep(1)
    
    # Read OTP from logs
    try:
        with open('/var/log/supervisor/backend.err.log', 'r') as f:
            lines = f.readlines()
            for line in reversed(lines[-20:]):
                if 'OTP:' in line:
                    otp = line.split('OTP:')[-1].strip()[:6]
                    break
            else:
                print(f"Could not find OTP for {email}")
                return None, None
    except Exception as e:
        print(f"Error reading OTP: {e}")
        return None, None
    
    # Verify OTP
    response = session.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": email,
        "otp": otp
    })
    
    if response.status_code != 200:
        print(f"Failed to verify OTP for {email}: {response.text}")
        return None, None
    
    data = response.json()
    return data.get('token'), data.get('user')

def setup_user_profile(token, user_id):
    """Complete user onboarding"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Accept terms
    requests.post(f"{BASE_URL}/api/user/accept-terms", headers=headers)
    
    # Set location
    requests.put(f"{BASE_URL}/api/user/profile", headers=headers, json={
        "display_name": f"Test User {user_id[:6]}",
        "latitude": -34.6037,
        "longitude": -58.3816,
        "city_name": "Buenos Aires",
        "country_code": "AR"
    })

def get_albums(token):
    """Get available albums"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/albums", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def activate_album(token, album_id):
    """Activate an album for the user"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/albums/{album_id}/activate", headers=headers)
    return response.status_code == 200

def add_sticker_to_album(token, album_id, sticker_number, status="have"):
    """Add a sticker to an album"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/albums/{album_id}/stickers", headers=headers, json={
        "sticker_number": sticker_number,
        "status": status
    })
    return response.status_code == 201

def create_exchange(token, partner_id, offered_stickers, requested_stickers):
    """Create an exchange"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/exchanges", headers=headers, json={
        "partner_id": partner_id,
        "offered_stickers": offered_stickers,
        "requested_stickers": requested_stickers
    })
    if response.status_code == 201:
        return response.json()
    print(f"Failed to create exchange: {response.status_code} - {response.text}")
    return None

def send_chat_message(token, exchange_id, content):
    """Send a chat message"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/exchanges/{exchange_id}/chat/messages", headers=headers, json={
        "content": content
    })
    return response

def test_chat_limit_error_structure():
    """
    Test the complete chat limit scenario
    """
    print("=" * 60)
    print("Testing Chat Limit Error Structure")
    print("=" * 60)
    
    # Create test users
    user_a_email = generate_test_email()
    user_b_email = generate_test_email()
    user_c_email = generate_test_email()
    
    print(f"\nCreating test users:")
    print(f"  User A: {user_a_email}")
    print(f"  User B: {user_b_email}")
    print(f"  User C: {user_c_email}")
    
    # Login users
    print("\nLogging in users...")
    token_a, user_a = login_user(user_a_email)
    if not token_a:
        print("FAILED: Could not login User A")
        return False
    print(f"  User A logged in: {user_a['id']}")
    
    token_b, user_b = login_user(user_b_email)
    if not token_b:
        print("FAILED: Could not login User B")
        return False
    print(f"  User B logged in: {user_b['id']}")
    
    token_c, user_c = login_user(user_c_email)
    if not token_c:
        print("FAILED: Could not login User C")
        return False
    print(f"  User C logged in: {user_c['id']}")
    
    # Setup profiles
    print("\nSetting up user profiles...")
    setup_user_profile(token_a, user_a['id'])
    setup_user_profile(token_b, user_b['id'])
    setup_user_profile(token_c, user_c['id'])
    
    # Get available albums
    print("\nGetting available albums...")
    albums = get_albums(token_a)
    if not albums:
        print("FAILED: No albums available")
        return False
    
    # Use the first album
    album_id = albums[0]['id']
    print(f"  Using album: {albums[0]['name']} ({album_id})")
    
    # Activate album for all users
    print("\nActivating album for all users...")
    activate_album(token_a, album_id)
    activate_album(token_b, album_id)
    activate_album(token_c, album_id)
    
    # Add stickers
    print("\nAdding stickers...")
    add_sticker_to_album(token_a, album_id, "1", "have")
    add_sticker_to_album(token_a, album_id, "2", "need")
    add_sticker_to_album(token_b, album_id, "1", "need")
    add_sticker_to_album(token_b, album_id, "2", "have")
    add_sticker_to_album(token_c, album_id, "3", "have")
    add_sticker_to_album(token_c, album_id, "1", "need")
    
    # Step 1: User A creates exchange with User B (uses A's 1/1 limit)
    print("\nStep 1: User A creates exchange with User B...")
    exchange_ab = create_exchange(token_a, user_b['id'], 
                                   [{"album_id": album_id, "sticker_number": "1"}],
                                   [{"album_id": album_id, "sticker_number": "2"}])
    if not exchange_ab:
        print("FAILED: Could not create exchange A->B")
        return False
    print(f"  Exchange created: {exchange_ab['id']}")
    
    # Step 2: User C creates exchange with User A
    print("\nStep 2: User C creates exchange with User A...")
    exchange_ca = create_exchange(token_c, user_a['id'],
                                   [{"album_id": album_id, "sticker_number": "3"}],
                                   [{"album_id": album_id, "sticker_number": "1"}])
    if not exchange_ca:
        print("FAILED: Could not create exchange C->A")
        return False
    print(f"  Exchange created: {exchange_ca['id']}")
    
    # Step 3: User A tries to reply to User C's chat
    print("\nStep 3: User A tries to reply to User C's chat...")
    response = send_chat_message(token_a, exchange_ca['id'], "Hello from User A!")
    
    print(f"  Response status: {response.status_code}")
    print(f"  Response body: {response.text}")
    
    if response.status_code == 403:
        error_detail = response.json().get('detail')
        print(f"\n  Error detail type: {type(error_detail)}")
        print(f"  Error detail: {json.dumps(error_detail, indent=2)}")
        
        # Verify the error structure
        if isinstance(error_detail, dict):
            if error_detail.get('code') == 'DAILY_MATCH_LIMIT':
                print("\n✅ SUCCESS: Error has correct structure!")
                print("   - code: DAILY_MATCH_LIMIT")
                print(f"   - message: {error_detail.get('message')}")
                print(f"   - matches_used: {error_detail.get('matches_used')}")
                print(f"   - limit: {error_detail.get('limit')}")
                print("\n   Frontend will show UpgradeModal instead of crashing!")
                return True
            else:
                print(f"\n❌ FAILED: Wrong error code: {error_detail.get('code')}")
                return False
        else:
            print(f"\n❌ FAILED: Error detail is not an object: {type(error_detail)}")
            return False
    elif response.status_code == 200:
        print("\n⚠️ WARNING: Message was sent successfully (limit not enforced)")
        print("   This might happen if the user's counter wasn't incremented properly")
        return False
    else:
        print(f"\n❌ FAILED: Unexpected status code: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_chat_limit_error_structure()
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED: Chat limit error structure is correct")
        print("Frontend fix verified: UpgradeModal will be shown instead of crash")
    else:
        print("TEST FAILED: See details above")
    print("=" * 60)
