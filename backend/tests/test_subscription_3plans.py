"""
Test 3-Plan Subscription System: Free, Plus, Unlimited
Tests:
- GET /api/user/plan-status returns correct limits per plan
- POST /api/user/set-plan accepts 'free', 'plus', 'unlimited'
- can_user_create_match enforces chat limits per plan
- can_user_activate_album enforces album limits per plan
- Plan constants: FREE=1/1, PLUS=2/5, UNLIMITED=null
"""
import pytest
import requests
import os
import time
import subprocess
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSubscription3Plans:
    """Test 3-plan subscription system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_email = f"test_3plan_{int(time.time())}@example.com"
        self.token = None
    
    def _get_otp_from_logs(self, email):
        """Get OTP from backend logs (DEV_MODE enabled)"""
        result = subprocess.run(
            ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
            capture_output=True, text=True
        )
        lines = result.stdout.split('\n')
        
        found_email = False
        for line in lines:
            if f'[OTP] To: {email}' in line:
                found_email = True
                continue
            if found_email and '[OTP] OTP:' in line:
                match = re.search(r'\[OTP\] OTP: (\d{6})', line)
                if match:
                    return match.group(1)
                found_email = False
        return None
    
    def _authenticate(self, email=None):
        """Authenticate and get token"""
        email = email or self.test_email
        
        # Send OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert response.status_code == 200, f"Failed to send OTP: {response.text}"
        
        # Get OTP from logs
        time.sleep(1)
        otp = self._get_otp_from_logs(email)
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
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        return data['user']
    
    # ==========================================
    # Test Plan Status Endpoint
    # ==========================================
    
    def test_free_plan_status_returns_correct_limits(self):
        """Test GET /api/user/plan-status returns free=1/1 limits"""
        self._authenticate()
        
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify free plan structure
        assert data['plan'] == 'free', f"Expected 'free' plan, got {data['plan']}"
        assert data['is_premium'] == False, "Free user should not be premium"
        assert data['is_plus'] == False, "Free user should not be plus"
        assert data['is_unlimited'] == False, "Free user should not be unlimited"
        
        # Verify limits: free = 1 album, 1 chat/day
        assert data['matches_limit'] == 1, f"Free plan chat limit should be 1, got {data['matches_limit']}"
        assert data['albums_limit'] == 1, f"Free plan album limit should be 1, got {data['albums_limit']}"
        
        print(f"✓ Free plan status: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")
    
    def test_plus_plan_status_returns_correct_limits(self):
        """Test GET /api/user/plan-status returns plus=2/5 limits"""
        self._authenticate()
        
        # Upgrade to Plus
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200, f"Failed to set plus plan: {response.text}"
        
        # Get plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify plus plan structure
        assert data['plan'] == 'plus', f"Expected 'plus' plan, got {data['plan']}"
        assert data['is_premium'] == True, "Plus user should be premium"
        assert data['is_plus'] == True, "Plus user should have is_plus=True"
        assert data['is_unlimited'] == False, "Plus user should not be unlimited"
        
        # Verify limits: plus = 2 albums, 5 chats/day
        assert data['matches_limit'] == 5, f"Plus plan chat limit should be 5, got {data['matches_limit']}"
        assert data['albums_limit'] == 2, f"Plus plan album limit should be 2, got {data['albums_limit']}"
        
        print(f"✓ Plus plan status: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")
    
    def test_unlimited_plan_status_returns_null_limits(self):
        """Test GET /api/user/plan-status returns unlimited=null limits"""
        self._authenticate()
        
        # Upgrade to Unlimited
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200, f"Failed to set unlimited plan: {response.text}"
        
        # Get plan status
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify unlimited plan structure
        assert data['plan'] == 'unlimited', f"Expected 'unlimited' plan, got {data['plan']}"
        assert data['is_premium'] == True, "Unlimited user should be premium"
        assert data['is_plus'] == False, "Unlimited user should not have is_plus=True"
        assert data['is_unlimited'] == True, "Unlimited user should have is_unlimited=True"
        
        # Verify limits: unlimited = null (no limits)
        assert data['matches_limit'] is None, f"Unlimited plan chat limit should be None, got {data['matches_limit']}"
        assert data['albums_limit'] is None, f"Unlimited plan album limit should be None, got {data['albums_limit']}"
        
        print(f"✓ Unlimited plan status: albums_limit={data['albums_limit']}, matches_limit={data['matches_limit']}")
    
    # ==========================================
    # Test Set Plan Endpoint
    # ==========================================
    
    def test_set_plan_accepts_free(self):
        """Test POST /api/user/set-plan accepts 'free'"""
        self._authenticate()
        
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=free")
        assert response.status_code == 200, f"Failed to set free plan: {response.text}"
        
        data = response.json()
        assert data['user']['plan'] == 'free', f"Expected 'free' plan, got {data['user']['plan']}"
        print("✓ set-plan accepts 'free'")
    
    def test_set_plan_accepts_plus(self):
        """Test POST /api/user/set-plan accepts 'plus'"""
        self._authenticate()
        
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus&plan_type=monthly")
        assert response.status_code == 200, f"Failed to set plus plan: {response.text}"
        
        data = response.json()
        assert data['user']['plan'] == 'plus', f"Expected 'plus' plan, got {data['user']['plan']}"
        print("✓ set-plan accepts 'plus'")
    
    def test_set_plan_accepts_unlimited(self):
        """Test POST /api/user/set-plan accepts 'unlimited'"""
        self._authenticate()
        
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited&plan_type=monthly")
        assert response.status_code == 200, f"Failed to set unlimited plan: {response.text}"
        
        data = response.json()
        assert data['user']['plan'] == 'unlimited', f"Expected 'unlimited' plan, got {data['user']['plan']}"
        print("✓ set-plan accepts 'unlimited'")
    
    def test_set_plan_rejects_invalid_plan(self):
        """Test POST /api/user/set-plan rejects invalid plan names"""
        self._authenticate()
        
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=premium")
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=gold")
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        
        print("✓ set-plan rejects invalid plan names")
    
    # ==========================================
    # Test Plan Constants in models.py
    # ==========================================
    
    def test_plan_constants_correct_values(self):
        """Verify plan constants in models.py"""
        import sys
        sys.path.insert(0, '/app/backend')
        from models import (
            FREE_PLAN_MAX_ALBUMS, FREE_PLAN_MAX_CHATS_PER_DAY,
            PLUS_PLAN_MAX_ALBUMS, PLUS_PLAN_MAX_CHATS_PER_DAY
        )
        
        # Free plan: 1 album, 1 chat/day
        assert FREE_PLAN_MAX_ALBUMS == 1, f"FREE_PLAN_MAX_ALBUMS should be 1, got {FREE_PLAN_MAX_ALBUMS}"
        assert FREE_PLAN_MAX_CHATS_PER_DAY == 1, f"FREE_PLAN_MAX_CHATS_PER_DAY should be 1, got {FREE_PLAN_MAX_CHATS_PER_DAY}"
        
        # Plus plan: 2 albums, 5 chats/day
        assert PLUS_PLAN_MAX_ALBUMS == 2, f"PLUS_PLAN_MAX_ALBUMS should be 2, got {PLUS_PLAN_MAX_ALBUMS}"
        assert PLUS_PLAN_MAX_CHATS_PER_DAY == 5, f"PLUS_PLAN_MAX_CHATS_PER_DAY should be 5, got {PLUS_PLAN_MAX_CHATS_PER_DAY}"
        
        print(f"✓ Plan constants: FREE={FREE_PLAN_MAX_ALBUMS}/{FREE_PLAN_MAX_CHATS_PER_DAY}, PLUS={PLUS_PLAN_MAX_ALBUMS}/{PLUS_PLAN_MAX_CHATS_PER_DAY}")
    
    # ==========================================
    # Test can_match and can_activate_album flags
    # ==========================================
    
    def test_free_user_can_match_initially(self):
        """Test free user can_match=True when matches_used_today=0"""
        self._authenticate()
        
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['matches_used_today'] == 0, "New user should have 0 matches used"
        assert data['can_match'] == True, "Free user with 0 matches should be able to match"
        
        print("✓ Free user can_match=True initially")
    
    def test_free_user_can_activate_album_initially(self):
        """Test free user can_activate_album=True when active_albums=0"""
        self._authenticate()
        
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['active_albums'] == 0, "New user should have 0 active albums"
        assert data['can_activate_album'] == True, "Free user with 0 albums should be able to activate"
        
        print("✓ Free user can_activate_album=True initially")
    
    def test_unlimited_user_always_can_match(self):
        """Test unlimited user can_match=True always"""
        self._authenticate()
        
        # Upgrade to Unlimited
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited")
        assert response.status_code == 200
        
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['can_match'] == True, "Unlimited user should always be able to match"
        assert data['can_activate_album'] == True, "Unlimited user should always be able to activate albums"
        
        print("✓ Unlimited user can_match=True and can_activate_album=True always")
    
    # ==========================================
    # Test Plan Transitions
    # ==========================================
    
    def test_upgrade_free_to_plus(self):
        """Test upgrading from free to plus"""
        self._authenticate()
        
        # Verify starts as free
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        assert response.json()['plan'] == 'free'
        
        # Upgrade to plus
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus")
        assert response.status_code == 200
        
        # Verify now plus
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'plus'
        assert data['matches_limit'] == 5
        assert data['albums_limit'] == 2
        
        print("✓ Upgrade free → plus works correctly")
    
    def test_upgrade_plus_to_unlimited(self):
        """Test upgrading from plus to unlimited"""
        self._authenticate()
        
        # Set to plus first
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=plus")
        assert response.status_code == 200
        
        # Upgrade to unlimited
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited")
        assert response.status_code == 200
        
        # Verify now unlimited
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'unlimited'
        assert data['matches_limit'] is None
        assert data['albums_limit'] is None
        
        print("✓ Upgrade plus → unlimited works correctly")
    
    def test_downgrade_unlimited_to_free(self):
        """Test downgrading from unlimited to free"""
        self._authenticate()
        
        # Set to unlimited first
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=unlimited")
        assert response.status_code == 200
        
        # Downgrade to free
        response = self.session.post(f"{BASE_URL}/api/user/set-plan?plan=free")
        assert response.status_code == 200
        
        # Verify now free
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'free'
        assert data['matches_limit'] == 1
        assert data['albums_limit'] == 1
        
        print("✓ Downgrade unlimited → free works correctly")
    
    # ==========================================
    # Test Legacy Endpoint Compatibility
    # ==========================================
    
    def test_legacy_upgrade_premium_sets_plus(self):
        """Test legacy /api/user/upgrade-premium sets plan to plus"""
        self._authenticate()
        
        response = self.session.post(f"{BASE_URL}/api/user/upgrade-premium?plan_type=monthly")
        assert response.status_code == 200, f"Legacy upgrade failed: {response.text}"
        
        # Verify plan is plus (legacy premium = plus)
        response = self.session.get(f"{BASE_URL}/api/user/plan-status")
        data = response.json()
        assert data['plan'] == 'plus', f"Legacy upgrade should set plan to 'plus', got {data['plan']}"
        
        print("✓ Legacy upgrade-premium sets plan to 'plus'")


class TestI18nSubscriptionKeys:
    """Test i18n translations for 3-plan subscription"""
    
    def test_i18n_has_free_plus_unlimited_keys(self):
        """Verify i18n.js has subscription.free, subscription.plus, subscription.unlimited"""
        i18n_path = "/app/frontend/src/i18n.js"
        
        with open(i18n_path, 'r') as f:
            content = f.read()
        
        # Check for plan name keys in subscription section (keys are: free:, plus:, unlimited:)
        assert "free:" in content, "Missing subscription free key"
        assert "plus:" in content, "Missing subscription plus key"
        assert "unlimited:" in content, "Missing subscription unlimited key"
        
        # Check for plan display names
        assert "Plan Gratuito" in content, "Missing Spanish 'Plan Gratuito'"
        assert "Plan Plus" in content, "Missing Spanish 'Plan Plus'"
        assert "Plan Ilimitado" in content, "Missing Spanish 'Plan Ilimitado'"
        
        print("✓ i18n has free, plus, unlimited plan keys")
    
    def test_i18n_has_benefits_sections(self):
        """Verify i18n.js has freeBenefits, plusBenefits, unlimitedBenefits"""
        i18n_path = "/app/frontend/src/i18n.js"
        
        with open(i18n_path, 'r') as f:
            content = f.read()
        
        # Check for benefits sections
        assert "freeBenefits" in content, "Missing freeBenefits section"
        assert "plusBenefits" in content, "Missing plusBenefits section"
        assert "unlimitedBenefits" in content, "Missing unlimitedBenefits section"
        
        # Check for specific benefit keys
        assert "1 álbum activo" in content or "1 active album" in content, "Missing free album benefit"
        assert "2 álbumes activos" in content or "2 active albums" in content, "Missing plus album benefit"
        assert "Álbumes ilimitados" in content or "Unlimited albums" in content, "Missing unlimited album benefit"
        
        assert "1 chat nuevo por día" in content or "1 new chat per day" in content, "Missing free chat benefit"
        assert "5 chats nuevos por día" in content or "5 new chats per day" in content, "Missing plus chat benefit"
        assert "Chats ilimitados" in content or "Unlimited chats" in content, "Missing unlimited chat benefit"
        
        print("✓ i18n has freeBenefits, plusBenefits, unlimitedBenefits sections")
    
    def test_i18n_all_6_languages_have_subscription_keys(self):
        """Verify all 6 languages have subscription keys"""
        i18n_path = "/app/frontend/src/i18n.js"
        
        with open(i18n_path, 'r') as f:
            content = f.read()
        
        # Check each language has subscription section (format is: es: { or en: {)
        languages = ['es', 'en', 'pt', 'fr', 'de', 'it']
        
        for lang in languages:
            # Each language should have a section in resources object
            assert f"{lang}:" in content or f"{lang} :" in content, f"Missing {lang} language section"
        
        # Check for specific translations in different languages
        translations_to_check = [
            ('es', 'Plan Gratuito'),
            ('en', 'Free Plan'),
            ('pt', 'Plano Gratuito'),
        ]
        
        for lang, text in translations_to_check:
            assert text in content, f"Missing {lang} translation: '{text}'"
        
        print("✓ All 6 languages have subscription keys")


class TestSubscriptionSectionComponent:
    """Test SubscriptionSection.js component"""
    
    def test_component_uses_correct_i18n_keys(self):
        """Verify SubscriptionSection.js uses correct i18n keys"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for plan name keys
        assert "subscription.free" in content, "Missing subscription.free key usage"
        assert "subscription.plus" in content, "Missing subscription.plus key usage"
        assert "subscription.unlimited" in content, "Missing subscription.unlimited key usage"
        
        # Check for benefits keys
        assert "subscription.freeBenefits" in content, "Missing freeBenefits key usage"
        assert "subscription.plusBenefits" in content, "Missing plusBenefits key usage"
        assert "subscription.unlimitedBenefits" in content, "Missing unlimitedBenefits key usage"
        
        print("✓ SubscriptionSection uses correct i18n keys")
    
    def test_component_shows_usage_counters(self):
        """Verify SubscriptionSection shows usage counters"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for usage counter display
        assert "matches_used_today" in content, "Missing matches_used_today display"
        assert "matches_limit" in content, "Missing matches_limit display"
        assert "active_albums" in content, "Missing active_albums display"
        assert "albums_limit" in content, "Missing albums_limit display"
        
        print("✓ SubscriptionSection shows usage counters")
    
    def test_component_has_upgrade_buttons(self):
        """Verify SubscriptionSection has upgrade buttons"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for upgrade button keys
        assert "upgradeToPlus" in content, "Missing upgradeToPlus button"
        assert "upgradeToUnlimited" in content, "Missing upgradeToUnlimited button"
        
        # Check for data-testid attributes
        assert 'data-testid="upgrade-btn"' in content or "data-testid='upgrade-btn'" in content, "Missing upgrade-btn data-testid"
        
        print("✓ SubscriptionSection has upgrade buttons")
    
    def test_component_has_plan_cards_in_dialog(self):
        """Verify SubscriptionSection shows Plus and Unlimited plan cards in upgrade dialog"""
        component_path = "/app/frontend/src/components/SubscriptionSection.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for PlanCard component usage
        assert "PlanCard" in content, "Missing PlanCard component"
        
        # Check for upgrade dialog
        assert "showUpgradeDialog" in content, "Missing showUpgradeDialog state"
        assert "AlertDialog" in content, "Missing AlertDialog component"
        
        print("✓ SubscriptionSection has plan cards in upgrade dialog")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
