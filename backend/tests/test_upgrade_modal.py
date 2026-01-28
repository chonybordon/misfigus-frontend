"""
Test suite for UpgradeModal functionality
Tests the new Plus/Unlimited plan system that replaces the old Premium paywall

NOTE: This test requires DEV_MODE to be enabled in backend to see OTP in logs.
The test creates users and tests plan upgrade flows.
"""
import pytest
import requests
import os
import time
import subprocess
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sticker-swap-1.preview.emergentagent.com')

def get_otp_from_logs(email):
    """Get OTP from backend logs for a specific email"""
    try:
        result = subprocess.run(
            ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
            capture_output=True, text=True, timeout=5
        )
        logs = result.stdout
        
        # Find OTP for this email
        lines = logs.split('\n')
        for i, line in enumerate(lines):
            if f'[OTP] To: {email}' in line:
                # Next line should have the OTP
                for j in range(i, min(i+3, len(lines))):
                    match = re.search(r'\[OTP\] OTP: (\d{6})', lines[j])
                    if match:
                        return match.group(1)
        return None
    except Exception as e:
        print(f"Error getting OTP from logs: {e}")
        return None


def create_authenticated_session(email_prefix="test"):
    """Create a new user and return authenticated session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    timestamp = int(time.time())
    email = f"{email_prefix}_{timestamp}@example.com"
    
    # Request OTP
    response = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
    if response.status_code != 200:
        raise Exception(f"Failed to send OTP: {response.text}")
    
    # Wait for OTP to be logged
    time.sleep(1)
    
    # Get OTP from logs
    otp = get_otp_from_logs(email)
    if not otp:
        raise Exception(f"Could not find OTP for {email} in logs")
    
    # Verify OTP
    response = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": otp})
    if response.status_code != 200:
        raise Exception(f"Failed to verify OTP: {response.text}")
    
    data = response.json()
    token = data.get('token')
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session, email, data.get('user')


class TestUpgradeModalBackend:
    """Backend API tests for upgrade modal functionality"""
    
    def test_01_new_user_has_free_plan(self):
        """Test that new users start with free plan"""
        session, email, user = create_authenticated_session("test_free")
        
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['plan'] == 'free', f"Expected free plan, got {data['plan']}"
        assert data['albums_limit'] == 1, "Free plan should have 1 album limit"
        assert data['matches_limit'] == 1, "Free plan should have 1 chat/day limit"
        print(f"✓ New user {email} has free plan with correct limits")
    
    def test_02_activate_first_album_success(self):
        """Test that free user can activate first album"""
        session, email, user = create_authenticated_session("test_album1")
        
        # Get albums
        response = session.get(f"{BASE_URL}/api/albums")
        assert response.status_code == 200
        albums = response.json()
        
        # Find first activatable album
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if not activatable:
            pytest.skip("No activatable albums found")
        
        album_id = activatable[0]['id']
        
        # Activate album
        response = session.post(f"{BASE_URL}/api/albums/{album_id}/activate")
        assert response.status_code == 200, f"Failed to activate first album: {response.text}"
        print(f"✓ Free user successfully activated first album: {album_id}")
    
    def test_03_activate_second_album_blocked_for_free(self):
        """Test that free user cannot activate second album - should get ALBUM_LIMIT error"""
        session, email, user = create_authenticated_session("test_album2")
        
        # Get albums
        response = session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        # Find two activatable albums
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if len(activatable) < 2:
            pytest.skip("Need at least 2 activatable albums")
        
        # Activate first album
        response = session.post(f"{BASE_URL}/api/albums/{activatable[0]['id']}/activate")
        assert response.status_code == 200
        
        # Try to activate second album - should fail with ALBUM_LIMIT
        response = session.post(f"{BASE_URL}/api/albums/{activatable[1]['id']}/activate")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        error_data = response.json()
        detail = error_data.get('detail', {})
        assert detail.get('code') == 'ALBUM_LIMIT', f"Expected ALBUM_LIMIT error, got {detail}"
        print("✓ Correctly blocked second album activation for free user with ALBUM_LIMIT error")
    
    def test_04_upgrade_to_plus_and_activate_second_album(self):
        """Test upgrading to Plus plan allows second album activation"""
        session, email, user = create_authenticated_session("test_plus")
        
        # Get albums
        response = session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if len(activatable) < 2:
            pytest.skip("Need at least 2 activatable albums")
        
        # Activate first album
        response = session.post(f"{BASE_URL}/api/albums/{activatable[0]['id']}/activate")
        assert response.status_code == 200
        
        # Upgrade to Plus (MOCKED)
        response = session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200, f"Failed to upgrade to Plus: {response.text}"
        
        # Verify plan changed
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'plus', f"Expected plus plan, got {data['plan']}"
        assert data['albums_limit'] == 2, "Plus plan should have 2 album limit"
        assert data['matches_limit'] == 5, "Plus plan should have 5 chats/day limit"
        
        # Now activate second album - should succeed
        response = session.post(f"{BASE_URL}/api/albums/{activatable[1]['id']}/activate")
        assert response.status_code == 200, f"Plus user should be able to activate second album: {response.text}"
        print("✓ Plus user successfully activated second album after upgrade")
    
    def test_05_plus_user_blocked_from_third_album(self):
        """Test that Plus user cannot activate third album"""
        session, email, user = create_authenticated_session("test_plus3")
        
        # Upgrade to Plus first
        response = session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200
        
        # Get albums
        response = session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if len(activatable) < 3:
            pytest.skip("Need at least 3 activatable albums")
        
        # Activate first two albums
        response = session.post(f"{BASE_URL}/api/albums/{activatable[0]['id']}/activate")
        assert response.status_code == 200
        response = session.post(f"{BASE_URL}/api/albums/{activatable[1]['id']}/activate")
        assert response.status_code == 200
        
        # Try to activate third album - should fail
        response = session.post(f"{BASE_URL}/api/albums/{activatable[2]['id']}/activate")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        error_data = response.json()
        detail = error_data.get('detail', {})
        assert detail.get('code') == 'ALBUM_LIMIT', f"Expected ALBUM_LIMIT error, got {detail}"
        print("✓ Correctly blocked third album activation for Plus user")
    
    def test_06_unlimited_user_can_activate_any_album(self):
        """Test that Unlimited user can activate any number of albums"""
        session, email, user = create_authenticated_session("test_unlimited")
        
        # Upgrade to Unlimited
        response = session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200
        
        # Verify plan
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'unlimited'
        assert data['albums_limit'] is None, "Unlimited plan should have no album limit"
        assert data['matches_limit'] is None, "Unlimited plan should have no chat limit"
        
        # Get albums
        response = session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        
        # Activate all available albums
        activated_count = 0
        for album in activatable[:4]:  # Test up to 4 albums
            response = session.post(f"{BASE_URL}/api/albums/{album['id']}/activate")
            if response.status_code == 200:
                activated_count += 1
        
        print(f"✓ Unlimited user activated {activated_count} albums without limit")
        assert activated_count >= 2, "Should be able to activate at least 2 albums"


class TestPlanBenefitsCorrectness:
    """Test that plan benefits match the new Plus/Unlimited system"""
    
    def test_free_plan_benefits(self):
        """Test FREE plan: 1 album, 1 chat/day"""
        session, email, user = create_authenticated_session("test_free_benefits")
        
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        
        assert data['plan'] == 'free'
        assert data['albums_limit'] == 1, f"Free: expected 1 album, got {data['albums_limit']}"
        assert data['matches_limit'] == 1, f"Free: expected 1 chat/day, got {data['matches_limit']}"
        print(f"✓ FREE plan benefits correct: {data['albums_limit']} album, {data['matches_limit']} chat/day")
    
    def test_plus_plan_benefits(self):
        """Test PLUS plan: 2 albums, 5 chats/day"""
        session, email, user = create_authenticated_session("test_plus_benefits")
        
        # Upgrade to Plus
        session.post(f"{BASE_URL}/api/user/set-plan?plan=plus")
        
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        
        assert data['plan'] == 'plus'
        assert data['albums_limit'] == 2, f"Plus: expected 2 albums, got {data['albums_limit']}"
        assert data['matches_limit'] == 5, f"Plus: expected 5 chats/day, got {data['matches_limit']}"
        print(f"✓ PLUS plan benefits correct: {data['albums_limit']} albums, {data['matches_limit']} chats/day")
    
    def test_unlimited_plan_benefits(self):
        """Test UNLIMITED plan: unlimited albums, unlimited chats"""
        session, email, user = create_authenticated_session("test_unlimited_benefits")
        
        # Upgrade to Unlimited
        session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited")
        
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        
        assert data['plan'] == 'unlimited'
        assert data['albums_limit'] is None, f"Unlimited: expected None albums, got {data['albums_limit']}"
        assert data['matches_limit'] is None, f"Unlimited: expected None chats, got {data['matches_limit']}"
        print(f"✓ UNLIMITED plan benefits correct: unlimited albums, unlimited chats")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
