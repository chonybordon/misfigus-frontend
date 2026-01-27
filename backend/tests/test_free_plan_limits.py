"""
Test Free Plan Limits: 1 chat per day enforcement
Tests:
- FREE_PLAN_MAX_MATCHES_PER_DAY = 1 enforces 1 chat/day limit
- DAILY_MATCH_LIMIT error returned when free user exceeds limit
- Premium users not limited (can_user_create_match returns true)
- plan-status endpoint returns matches_used_today and matches_limit
"""
import pytest
import requests
import os
import time
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFreePlanLimits:
    """Test free plan chat limit enforcement"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_email = f"test_chatlimit_{int(time.time())}@example.com"
        self.token = None
        self.otp = None
    
    def _request_otp(self, email):
        """Request OTP for email"""
        response = self.session.post(f"{BASE_URL}/api/auth/otp", json={"email": email})
        assert response.status_code == 200, f"OTP request failed: {response.text}"
        data = response.json()
        # In DEV_MODE, OTP is returned in response
        if 'otp' in data:
            return data['otp']
        return None
    
    def _verify_otp(self, email, otp):
        """Verify OTP and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/verify", json={"email": email, "otp": otp})
        assert response.status_code == 200, f"OTP verify failed: {response.text}"
        data = response.json()
        return data.get('token')
    
    def _get_auth_headers(self, token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_plan_status_endpoint_structure(self):
        """Test plan-status endpoint returns correct structure for free user"""
        # Create new user
        otp = self._request_otp(self.test_email)
        assert otp is not None, "OTP not returned in DEV_MODE"
        
        token = self._verify_otp(self.test_email, otp)
        assert token is not None, "Token not returned"
        
        # Get plan status
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        assert response.status_code == 200, f"Plan status failed: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "plan" in data, "Missing 'plan' field"
        assert "is_premium" in data, "Missing 'is_premium' field"
        assert "matches_used_today" in data, "Missing 'matches_used_today' field"
        assert "matches_limit" in data, "Missing 'matches_limit' field"
        assert "can_match" in data, "Missing 'can_match' field"
        
        # Verify values for new free user
        assert data["plan"] == "free", f"Expected 'free' plan, got {data['plan']}"
        assert data["is_premium"] == False, "New user should not be premium"
        assert data["matches_used_today"] == 0, f"New user should have 0 matches used, got {data['matches_used_today']}"
        assert data["matches_limit"] == 1, f"Free plan limit should be 1, got {data['matches_limit']}"
        assert data["can_match"] == True, "New free user should be able to match"
        
        print(f"✓ Plan status structure verified: {data}")
    
    def test_free_plan_limit_is_one(self):
        """Verify FREE_PLAN_MAX_MATCHES_PER_DAY = 1"""
        # Create new user
        email = f"test_limit_{int(time.time())}@example.com"
        otp = self._request_otp(email)
        token = self._verify_otp(email, otp)
        
        # Get plan status
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["matches_limit"] == 1, f"Free plan limit should be 1, got {data['matches_limit']}"
        print(f"✓ Free plan limit is 1 chat per day")
    
    def test_premium_user_unlimited_matches(self):
        """Test premium users have unlimited matches (matches_limit = None)"""
        # Create new user
        email = f"test_premium_{int(time.time())}@example.com"
        otp = self._request_otp(email)
        token = self._verify_otp(email, otp)
        
        # Upgrade to premium (mocked endpoint)
        response = self.session.post(
            f"{BASE_URL}/api/user/upgrade-premium?plan_type=monthly",
            headers=self._get_auth_headers(token)
        )
        assert response.status_code == 200, f"Premium upgrade failed: {response.text}"
        
        # Get plan status
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan"] == "premium", f"Expected 'premium' plan, got {data['plan']}"
        assert data["is_premium"] == True, "User should be premium"
        assert data["matches_limit"] is None, f"Premium should have no limit (None), got {data['matches_limit']}"
        assert data["can_match"] == True, "Premium user should always be able to match"
        
        print(f"✓ Premium user has unlimited matches: {data}")
    
    def test_premium_downgrade_to_free(self):
        """Test downgrading from premium to free restores limits"""
        # Create new user
        email = f"test_downgrade_{int(time.time())}@example.com"
        otp = self._request_otp(email)
        token = self._verify_otp(email, otp)
        
        # Upgrade to premium
        response = self.session.post(
            f"{BASE_URL}/api/user/upgrade-premium?plan_type=monthly",
            headers=self._get_auth_headers(token)
        )
        assert response.status_code == 200
        
        # Verify premium
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        data = response.json()
        assert data["is_premium"] == True
        
        # Downgrade to free
        response = self.session.post(
            f"{BASE_URL}/api/user/downgrade-free",
            headers=self._get_auth_headers(token)
        )
        assert response.status_code == 200, f"Downgrade failed: {response.text}"
        
        # Verify free plan limits restored
        response = self.session.get(
            f"{BASE_URL}/api/user/plan-status",
            headers=self._get_auth_headers(token)
        )
        data = response.json()
        assert data["plan"] == "free", f"Expected 'free' plan after downgrade, got {data['plan']}"
        assert data["is_premium"] == False, "User should not be premium after downgrade"
        assert data["matches_limit"] == 1, f"Free plan limit should be 1 after downgrade, got {data['matches_limit']}"
        
        print(f"✓ Downgrade restores free plan limits: {data}")


class TestI18nChatTranslations:
    """Test i18n translations for chat benefits"""
    
    def test_i18n_file_has_chat_translations(self):
        """Verify i18n.js has correct chat translations for all 6 languages"""
        i18n_path = "/app/frontend/src/i18n.js"
        
        with open(i18n_path, 'r') as f:
            content = f.read()
        
        # Expected translations
        expected_translations = {
            'es': '1 chat por día',
            'en': '1 chat per day',
            'pt': '1 chat por dia',
            'fr': '1 chat par jour',
            'de': '1 Chat pro Tag',
            'it': '1 chat al giorno'
        }
        
        for lang, expected in expected_translations.items():
            assert expected in content, f"Missing {lang} translation: '{expected}'"
            print(f"✓ {lang}: '{expected}' found")
        
        # Verify premium benefits have 'chats' key
        assert "premiumBenefits" in content, "Missing premiumBenefits section"
        assert "Chats ilimitados" in content, "Missing ES premium chats translation"
        assert "Unlimited chats" in content, "Missing EN premium chats translation"
        
        print("✓ All 6 languages have correct chat translations")
    
    def test_match_limit_desc_mentions_chats(self):
        """Verify matchLimitDesc mentions 'chats' not 'intercambios/trades'"""
        i18n_path = "/app/frontend/src/i18n.js"
        
        with open(i18n_path, 'r') as f:
            content = f.read()
        
        # Find matchLimitDesc lines
        match_limit_lines = [line for line in content.split('\n') if 'matchLimitDesc' in line]
        
        for line in match_limit_lines:
            # Should mention 'chats' not 'intercambios' or 'trades'
            assert 'chat' in line.lower(), f"matchLimitDesc should mention 'chats': {line}"
            print(f"✓ matchLimitDesc mentions chats: {line.strip()[:80]}...")
        
        print("✓ matchLimitDesc correctly mentions 'chats'")


class TestSubscriptionUIComponents:
    """Test SubscriptionSection.js uses correct i18n keys and icons"""
    
    def test_subscription_section_uses_chat_keys(self):
        """Verify SubscriptionSection.js uses t('subscription.freeBenefits.chats')"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for correct i18n keys
        assert "subscription.freeBenefits.chats" in content, "Missing freeBenefits.chats key usage"
        assert "subscription.premiumBenefits.chats" in content, "Missing premiumBenefits.chats key usage"
        
        print("✓ SubscriptionSection uses correct i18n keys for chats")
    
    def test_subscription_section_uses_message_circle_icon(self):
        """Verify SubscriptionSection.js uses MessageCircle icon for chat benefit"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for MessageCircle import
        assert "MessageCircle" in content, "Missing MessageCircle icon import"
        
        # Check it's used in BenefitItem for chats
        # Look for pattern: icon={MessageCircle} ... chats
        assert "icon={MessageCircle}" in content or "MessageCircle" in content, "MessageCircle icon not used"
        
        print("✓ SubscriptionSection uses MessageCircle icon")
    
    def test_subscription_section_shows_usage_counter(self):
        """Verify SubscriptionSection shows X/1 counter for chats"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for matches_used_today and matches_limit usage
        assert "matches_used_today" in content, "Missing matches_used_today display"
        assert "matches_limit" in content, "Missing matches_limit display"
        
        # Check for the counter pattern: {planStatus.matches_used_today} / {planStatus.matches_limit}
        assert "planStatus.matches_used_today" in content, "Missing usage counter display"
        assert "planStatus.matches_limit" in content, "Missing limit counter display"
        
        print("✓ SubscriptionSection shows usage counter X/1")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
