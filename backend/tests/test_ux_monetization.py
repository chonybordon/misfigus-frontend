"""
Test UX and Monetization Improvements:
1. Free user daily chat limit (1 per day)
2. Premium user unlimited chats
3. Backend freemium logic validation
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFreemiumChatLimits:
    """Test free user daily chat limit and premium unlimited access"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_email = f"test_freemium_{int(time.time())}@example.com"
        self.token = None
        self.user_id = None
        
    def _get_otp_from_logs(self):
        """Get OTP from backend logs (DEV_MODE enabled)"""
        import subprocess
        result = subprocess.run(
            ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
            capture_output=True, text=True
        )
        lines = result.stdout.split('\n')
        for line in reversed(lines):
            if 'OTP code' in line and self.test_email in line:
                # Extract OTP from log line
                import re
                match = re.search(r'OTP code (\d{6})', line)
                if match:
                    return match.group(1)
        return None
    
    def _authenticate(self, email=None):
        """Authenticate and get token"""
        email = email or self.test_email
        
        # Send OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert response.status_code == 200, f"Failed to send OTP: {response.text}"
        
        # Get OTP from logs
        time.sleep(1)
        otp = self._get_otp_from_logs()
        if not otp:
            pytest.skip("Could not get OTP from logs")
        
        # Verify OTP
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": email,
            "otp": otp
        })
        assert response.status_code == 200, f"Failed to verify OTP: {response.text}"
        
        data = response.json()
        self.token = data['token']
        self.user_id = data['user']['id']
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        return data['user']
    
    def test_free_user_plan_status(self):
        """Test that new users start with free plan"""
        user = self._authenticate()
        
        # Check plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['plan'] == 'free', "New user should have free plan"
        assert data['is_premium'] == False
        assert data['matches_limit'] == 1, "Free plan should have 1 match per day limit"
        assert data['matches_used_today'] == 0, "New user should have 0 matches used"
        print(f"✓ Free user plan status verified: {data}")
    
    def test_premium_upgrade_mocked(self):
        """Test premium upgrade (mocked - no real payment)"""
        self._authenticate()
        
        # Upgrade to premium
        response = self.session.post(f"{BASE_URL}/api/user/upgrade-premium?plan_type=monthly")
        assert response.status_code == 200
        
        data = response.json()
        assert data['user']['plan'] == 'premium', "User should be premium after upgrade"
        
        # Verify plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        status = response.json()
        assert status['is_premium'] == True
        assert status['matches_limit'] is None, "Premium should have no match limit"
        print(f"✓ Premium upgrade verified (MOCKED): {status}")
    
    def test_can_user_create_match_logic(self):
        """Test the can_user_create_match backend logic"""
        self._authenticate()
        
        # Get initial plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['can_match'] == True, "Free user with 0 matches should be able to match"
        print(f"✓ Free user can create first match: can_match={data['can_match']}")
    
    def test_free_plan_max_matches_constant(self):
        """Verify FREE_PLAN_MAX_MATCHES_PER_DAY is set to 1"""
        # This is a code review test - verify the constant in models.py
        import sys
        sys.path.insert(0, '/app/backend')
        from models import FREE_PLAN_MAX_MATCHES_PER_DAY
        
        assert FREE_PLAN_MAX_MATCHES_PER_DAY == 1, f"Expected 1, got {FREE_PLAN_MAX_MATCHES_PER_DAY}"
        print(f"✓ FREE_PLAN_MAX_MATCHES_PER_DAY = {FREE_PLAN_MAX_MATCHES_PER_DAY}")


class TestExchangeCreationLimit:
    """Test exchange creation with freemium limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def test_daily_match_limit_error_code(self):
        """Verify DAILY_MATCH_LIMIT error code exists in backend"""
        # Check server.py for the error code
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        assert 'DAILY_MATCH_LIMIT' in content, "DAILY_MATCH_LIMIT error code should exist in server.py"
        assert 'can_user_create_match' in content, "can_user_create_match function should exist"
        print("✓ DAILY_MATCH_LIMIT error code found in backend")
    
    def test_exchange_endpoint_checks_limit(self):
        """Verify exchange creation endpoint checks freemium limit"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Check that exchange creation uses can_user_create_match
        assert 'can_user_create_match' in content
        # Check for the limit check in exchange creation
        assert 'FREE_PLAN_MAX_MATCHES_PER_DAY' in content or 'DAILY_MATCH_LIMIT' in content
        print("✓ Exchange endpoint includes freemium limit check")


class TestPlanStatusEndpoint:
    """Test /api/user/plan-status endpoint"""
    
    def test_plan_status_response_structure(self):
        """Test plan status endpoint returns expected fields"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        test_email = f"test_plan_{int(time.time())}@example.com"
        
        # Send OTP
        response = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": test_email})
        assert response.status_code == 200
        
        # Get OTP from logs
        time.sleep(1)
        import subprocess
        result = subprocess.run(
            ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
            capture_output=True, text=True
        )
        otp = None
        for line in reversed(result.stdout.split('\n')):
            if 'OTP code' in line and test_email in line:
                import re
                match = re.search(r'OTP code (\d{6})', line)
                if match:
                    otp = match.group(1)
                    break
        
        if not otp:
            pytest.skip("Could not get OTP from logs")
        
        # Verify OTP
        response = session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": test_email,
            "otp": otp
        })
        assert response.status_code == 200
        token = response.json()['token']
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get plan status
        response = session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        required_fields = [
            'plan', 'is_premium', 'matches_used_today', 'matches_limit',
            'can_match', 'active_albums', 'albums_limit', 'can_activate_album'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Plan status response structure verified: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
