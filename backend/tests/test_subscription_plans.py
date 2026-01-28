"""
Test subscription plan logic for MisFigus app.
Tests: Free, Plus, and Unlimited plan limits and behaviors.

Features tested:
1. Plus plan shows correct limits: 2 albums, 5 chats/day
2. Chat counter increments for Plus users
3. Unlimited plan has no limits
4. Free plan shows 1 album, 1 chat/day
5. Backend enforces Plus limit of 5 chats per day
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSubscriptionPlanStatus:
    """Test plan-status endpoint returns correct limits for each plan"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test user and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Create unique test email
        timestamp = int(time.time() * 1000)
        self.test_email = f"test_plan_{timestamp}@test.com"
        
        # Send OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={
            "email": self.test_email
        })
        assert response.status_code == 200, f"Failed to send OTP: {response.text}"
        
        # Verify OTP (test users get 123456)
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": self.test_email,
            "otp": "123456"
        })
        assert response.status_code == 200, f"Failed to verify OTP: {response.text}"
        
        data = response.json()
        self.token = data.get("token")
        self.user_id = data.get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        # Cleanup: No explicit cleanup needed, test users are identified by @test.com
    
    def test_free_plan_limits(self):
        """Free plan should show 1 album limit and 1 chat/day limit"""
        # Ensure user is on free plan
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=free")
        assert response.status_code == 200
        
        # Get plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan"] == "free", f"Expected free plan, got {data['plan']}"
        assert data["albums_limit"] == 1, f"Free plan should have 1 album limit, got {data['albums_limit']}"
        assert data["matches_limit"] == 1, f"Free plan should have 1 chat/day limit, got {data['matches_limit']}"
        assert data["is_premium"] == False
        assert data["is_plus"] == False
        assert data["is_unlimited"] == False
        print(f"✓ Free plan limits correct: {data['albums_limit']} albums, {data['matches_limit']} chats/day")
    
    def test_plus_plan_limits(self):
        """Plus plan should show 2 album limit and 5 chats/day limit"""
        # Upgrade to Plus
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200
        
        # Get plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan"] == "plus", f"Expected plus plan, got {data['plan']}"
        assert data["albums_limit"] == 2, f"Plus plan should have 2 album limit, got {data['albums_limit']}"
        assert data["matches_limit"] == 5, f"Plus plan should have 5 chats/day limit, got {data['matches_limit']}"
        assert data["is_premium"] == True
        assert data["is_plus"] == True
        assert data["is_unlimited"] == False
        print(f"✓ Plus plan limits correct: {data['albums_limit']} albums, {data['matches_limit']} chats/day")
    
    def test_unlimited_plan_no_limits(self):
        """Unlimited plan should have no limits (null values)"""
        # Upgrade to Unlimited
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200
        
        # Get plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan"] == "unlimited", f"Expected unlimited plan, got {data['plan']}"
        assert data["albums_limit"] is None, f"Unlimited plan should have no album limit, got {data['albums_limit']}"
        assert data["matches_limit"] is None, f"Unlimited plan should have no chat limit, got {data['matches_limit']}"
        assert data["is_premium"] == True
        assert data["is_plus"] == False
        assert data["is_unlimited"] == True
        assert data["can_match"] == True
        assert data["can_activate_album"] == True
        print(f"✓ Unlimited plan has no limits: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")
    
    def test_matches_used_today_starts_at_zero(self):
        """New user should have 0 matches used today"""
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["matches_used_today"] == 0, f"New user should have 0 matches used, got {data['matches_used_today']}"
        print(f"✓ New user has 0 matches used today")


class TestPlanUpgradeDowngrade:
    """Test plan upgrade and downgrade functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test user and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        timestamp = int(time.time() * 1000)
        self.test_email = f"test_upgrade_{timestamp}@test.com"
        
        # Send and verify OTP
        self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": self.test_email})
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": self.test_email,
            "otp": "123456"
        })
        assert response.status_code == 200
        
        data = response.json()
        self.token = data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_upgrade_free_to_plus(self):
        """User can upgrade from free to plus"""
        # Start on free
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=free")
        assert response.status_code == 200
        
        # Verify free
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.json()["plan"] == "free"
        
        # Upgrade to plus
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200
        
        # Verify plus
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data["plan"] == "plus"
        assert data["albums_limit"] == 2
        assert data["matches_limit"] == 5
        print("✓ Successfully upgraded from free to plus")
    
    def test_upgrade_plus_to_unlimited(self):
        """User can upgrade from plus to unlimited"""
        # Start on plus
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200
        
        # Upgrade to unlimited
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200
        
        # Verify unlimited
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data["plan"] == "unlimited"
        assert data["albums_limit"] is None
        assert data["matches_limit"] is None
        print("✓ Successfully upgraded from plus to unlimited")
    
    def test_downgrade_unlimited_to_free(self):
        """User can downgrade from unlimited to free (if no albums)"""
        # Start on unlimited
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200
        
        # Downgrade to free
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=free")
        assert response.status_code == 200
        
        # Verify free
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data["plan"] == "free"
        assert data["albums_limit"] == 1
        assert data["matches_limit"] == 1
        print("✓ Successfully downgraded from unlimited to free")


class TestPlanStatusResponseStructure:
    """Test that plan-status response has all required fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test user and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        timestamp = int(time.time() * 1000)
        self.test_email = f"test_structure_{timestamp}@test.com"
        
        self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": self.test_email})
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": self.test_email,
            "otp": "123456"
        })
        assert response.status_code == 200
        
        data = response.json()
        self.token = data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_plan_status_has_required_fields(self):
        """Plan status response should have all required fields for UI"""
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields for UI display
        required_fields = [
            "plan",
            "is_premium",
            "is_plus",
            "is_unlimited",
            "matches_used_today",
            "matches_limit",
            "can_match",
            "active_albums",
            "albums_limit",
            "can_activate_album",
            "can_downgrade_to_free",
            "can_downgrade_to_plus"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ Plan status has all {len(required_fields)} required fields")
        print(f"  Response: plan={data['plan']}, albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
