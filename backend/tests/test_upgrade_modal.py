"""
Test suite for UpgradeModal functionality
Tests the new Plus/Unlimited plan system that replaces the old Premium paywall
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sticker-swap-1.preview.emergentagent.com')

class TestUpgradeModalBackend:
    """Backend API tests for upgrade modal functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Create unique test email
        timestamp = int(time.time())
        self.test_email = f"test_upgrade_{timestamp}@example.com"
        
        # Request OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": self.test_email})
        assert response.status_code == 200, f"Failed to send OTP: {response.text}"
        
        # Get OTP from response (DEV_MODE returns it)
        otp_data = response.json()
        self.otp = otp_data.get('otp')
        
        if not self.otp:
            pytest.skip("OTP not returned in response - check DEV_MODE setting")
        
        # Verify OTP and get token
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": self.test_email,
            "otp": self.otp
        })
        assert response.status_code == 200, f"Failed to verify OTP: {response.text}"
        
        data = response.json()
        self.token = data.get('token')
        self.user = data.get('user')
        
        # Set auth header
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        # Cleanup - no specific cleanup needed
    
    def test_01_new_user_has_free_plan(self):
        """Test that new users start with free plan"""
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['plan'] == 'free', f"Expected free plan, got {data['plan']}"
        assert data['albums_limit'] == 1, "Free plan should have 1 album limit"
        assert data['matches_limit'] == 1, "Free plan should have 1 chat/day limit"
    
    def test_02_get_albums_list(self):
        """Test getting list of available albums"""
        response = self.session.get(f"{BASE_URL}/api/albums")
        assert response.status_code == 200
        
        albums = response.json()
        assert len(albums) > 0, "Should have at least one album"
        
        # Store album IDs for later tests
        self.album_ids = [album['id'] for album in albums if album.get('user_state') != 'coming_soon']
        print(f"Found {len(self.album_ids)} activatable albums")
    
    def test_03_activate_first_album_success(self):
        """Test that free user can activate first album"""
        # Get albums
        response = self.session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        # Find first activatable album
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if not activatable:
            pytest.skip("No activatable albums found")
        
        album_id = activatable[0]['id']
        
        # Activate album
        response = self.session.post(f"{BASE_URL}/api/albums/{album_id}/activate")
        assert response.status_code == 200, f"Failed to activate first album: {response.text}"
        print(f"Successfully activated first album: {album_id}")
    
    def test_04_activate_second_album_blocked_for_free(self):
        """Test that free user cannot activate second album - should get ALBUM_LIMIT error"""
        # Get albums
        response = self.session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        # Find second activatable album
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if not activatable:
            pytest.skip("No second activatable album found")
        
        album_id = activatable[0]['id']
        
        # Try to activate second album - should fail with ALBUM_LIMIT
        response = self.session.post(f"{BASE_URL}/api/albums/{album_id}/activate")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        error_data = response.json()
        detail = error_data.get('detail', {})
        assert detail.get('code') == 'ALBUM_LIMIT', f"Expected ALBUM_LIMIT error, got {detail}"
        print("Correctly blocked second album activation for free user")
    
    def test_05_upgrade_to_plus_plan(self):
        """Test upgrading to Plus plan (MOCKED - no real payment)"""
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200, f"Failed to upgrade to Plus: {response.text}"
        
        # Verify plan changed
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'plus', f"Expected plus plan, got {data['plan']}"
        assert data['albums_limit'] == 2, "Plus plan should have 2 album limit"
        assert data['matches_limit'] == 5, "Plus plan should have 5 chats/day limit"
        print("Successfully upgraded to Plus plan")
    
    def test_06_plus_user_can_activate_second_album(self):
        """Test that Plus user can activate second album"""
        # Get albums
        response = self.session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        # Find second activatable album
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if not activatable:
            pytest.skip("No second activatable album found")
        
        album_id = activatable[0]['id']
        
        # Activate second album - should succeed for Plus user
        response = self.session.post(f"{BASE_URL}/api/albums/{album_id}/activate")
        assert response.status_code == 200, f"Plus user should be able to activate second album: {response.text}"
        print(f"Plus user successfully activated second album: {album_id}")
    
    def test_07_plus_user_blocked_from_third_album(self):
        """Test that Plus user cannot activate third album"""
        # Get albums
        response = self.session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        # Find third activatable album
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if not activatable:
            pytest.skip("No third activatable album found")
        
        album_id = activatable[0]['id']
        
        # Try to activate third album - should fail with ALBUM_LIMIT
        response = self.session.post(f"{BASE_URL}/api/albums/{album_id}/activate")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        error_data = response.json()
        detail = error_data.get('detail', {})
        assert detail.get('code') == 'ALBUM_LIMIT', f"Expected ALBUM_LIMIT error, got {detail}"
        print("Correctly blocked third album activation for Plus user")
    
    def test_08_upgrade_to_unlimited_plan(self):
        """Test upgrading to Unlimited plan (MOCKED - no real payment)"""
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200, f"Failed to upgrade to Unlimited: {response.text}"
        
        # Verify plan changed
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'unlimited', f"Expected unlimited plan, got {data['plan']}"
        assert data['albums_limit'] is None, "Unlimited plan should have no album limit"
        assert data['matches_limit'] is None, "Unlimited plan should have no chat limit"
        print("Successfully upgraded to Unlimited plan")
    
    def test_09_unlimited_user_can_activate_any_album(self):
        """Test that Unlimited user can activate any album"""
        # Get albums
        response = self.session.get(f"{BASE_URL}/api/albums")
        albums = response.json()
        
        # Find any activatable album
        activatable = [a for a in albums if a.get('user_state') == 'inactive']
        if not activatable:
            print("All albums already activated - test passed by default")
            return
        
        album_id = activatable[0]['id']
        
        # Activate album - should succeed for Unlimited user
        response = self.session.post(f"{BASE_URL}/api/albums/{album_id}/activate")
        assert response.status_code == 200, f"Unlimited user should be able to activate any album: {response.text}"
        print(f"Unlimited user successfully activated album: {album_id}")


class TestPlanBenefitsAPI:
    """Test plan benefits returned by API"""
    
    def test_plan_status_returns_correct_benefits(self):
        """Test that plan-status endpoint returns correct benefits for each plan"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Create test user
        timestamp = int(time.time())
        test_email = f"test_benefits_{timestamp}@example.com"
        
        # Request and verify OTP
        response = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": test_email})
        assert response.status_code == 200
        otp = response.json().get('otp')
        
        if not otp:
            pytest.skip("OTP not returned - check DEV_MODE")
        
        response = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": test_email, "otp": otp})
        assert response.status_code == 200
        token = response.json().get('token')
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test FREE plan benefits
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'free'
        assert data['albums_limit'] == 1
        assert data['matches_limit'] == 1
        print(f"FREE plan: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")
        
        # Test PLUS plan benefits
        session.post(f"{BASE_URL}/api/user/set-plan?plan=plus")
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'plus'
        assert data['albums_limit'] == 2
        assert data['matches_limit'] == 5
        print(f"PLUS plan: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")
        
        # Test UNLIMITED plan benefits
        session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited")
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'unlimited'
        assert data['albums_limit'] is None
        assert data['matches_limit'] is None
        print(f"UNLIMITED plan: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
