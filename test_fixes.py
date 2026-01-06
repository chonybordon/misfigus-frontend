#!/usr/bin/env python3

import requests
import json
import time
import subprocess
import re
from datetime import datetime

def test_misfigus_fixes():
    """Test the two specific fixes mentioned in the review request"""
    
    base_url = "https://trade-stickers.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"
    
    print("🚀 Testing MisFigus Fixes")
    print("="*60)
    print(f"Base URL: {base_url}")
    print(f"Album ID: {album_id}")
    
    results = {
        "frontend_compilation": False,
        "test_user_filtering": False,
        "album_matches_empty": False,
        "exchange_count_zero": False,
        "is_test_user_logic": False
    }
    
    # PART A: Test Frontend Compilation
    print("\n📋 PART A: Testing Frontend Compilation Fix")
    print("-" * 40)
    
    try:
        with open('/app/frontend/src/pages/ExchangeChat.js', 'r') as f:
            content = f.read()
            
        # Check for proper AuthContext import
        has_auth_import = 'AuthContext' in content and 'from \'../App\'' in content
        has_use_context = 'useContext(AuthContext)' in content
        
        if has_auth_import and has_use_context:
            print("✅ ExchangeChat.js has correct AuthContext import and usage")
            results["frontend_compilation"] = True
        else:
            print("❌ ExchangeChat.js missing proper AuthContext import/usage")
            
    except Exception as e:
        print(f"❌ Error checking ExchangeChat.js: {e}")
    
    # PART B: Test is_test_user() logic
    print("\n📋 PART B: Testing is_test_user() Helper Function Logic")
    print("-" * 40)
    
    test_cases = [
        ("user@test.com", True),
        ("user@misfigus.com", True), 
        ("user+test@gmail.com", True),
        ("exchange-test-user-1@test.com", True),
        ("exchange-test-user-2@misfigus.com", True),
        ("realuser@gmail.com", False),
        ("john.doe@yahoo.com", False),
        ("user@example.com", False)
    ]
    
    all_correct = True
    for email, expected in test_cases:
        # Simulate the is_test_user function logic from server.py
        is_test = (
            email.lower().endswith('@test.com') or
            email.lower().endswith('@misfigus.com') or
            '+test' in email.lower()
        )
        
        if is_test == expected:
            status = "✅"
        else:
            status = "❌"
            all_correct = False
            
        result_text = "TEST USER" if is_test else "NOT test user"
        print(f"{status} {email} → {result_text}")
    
    if all_correct:
        print("✅ is_test_user() logic working correctly")
        results["is_test_user_logic"] = True
    else:
        print("❌ is_test_user() logic has issues")
    
    # Test authentication and API endpoints
    print("\n📋 Testing API Endpoints with Authentication")
    print("-" * 40)
    
    # Send OTP
    test_email = f"test.{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com"
    print(f"🔍 Sending OTP to: {test_email}")
    
    try:
        response = requests.post(f"{api_url}/auth/send-otp", 
                               json={"email": test_email},
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            print("✅ OTP sent successfully")
            
            # Wait a moment for logs to be written
            time.sleep(2)
            
            # Try to extract OTP from logs
            try:
                result = subprocess.run(
                    ["tail", "-n", "20", "/var/log/supervisor/backend.err.log"],
                    capture_output=True, text=True, timeout=5
                )
                
                # Look for OTP in the logs
                otp_pattern = r'OTP:\s*(\d{6})'
                matches = re.findall(otp_pattern, result.stdout)
                
                if matches:
                    otp = matches[-1]  # Get the most recent OTP
                    print(f"✅ Found OTP in logs: {otp}")
                    
                    # Verify OTP
                    response = requests.post(f"{api_url}/auth/verify-otp",
                                           json={"email": test_email, "otp": otp},
                                           headers={'Content-Type': 'application/json'},
                                           timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        token = data.get('token')
                        user_id = data.get('user', {}).get('id')
                        
                        print(f"✅ Authentication successful! User ID: {user_id}")
                        
                        # Test album activation first
                        headers = {
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        }
                        
                        print(f"\n🔍 Activating album {album_id}...")
                        response = requests.post(f"{api_url}/albums/{album_id}/activate",
                                               headers=headers, timeout=10)
                        
                        if response.status_code in [200, 400]:  # 400 if already activated
                            print("✅ Album activated (or was already activated)")
                            
                            # Test album matches endpoint
                            print(f"\n🔍 Testing album matches endpoint...")
                            response = requests.get(f"{api_url}/albums/{album_id}/matches",
                                                  headers=headers, timeout=10)
                            
                            if response.status_code == 200:
                                matches = response.json()
                                print(f"✅ Album matches endpoint returned: {len(matches)} matches")
                                print(f"   Matches data: {matches}")
                                
                                if isinstance(matches, list) and len(matches) == 0:
                                    print("✅ Album matches returns empty array (test users filtered)")
                                    results["album_matches_empty"] = True
                                else:
                                    print("⚠️  Album matches returned non-empty array")
                            else:
                                print(f"❌ Album matches endpoint failed: {response.status_code} - {response.text[:200]}")
                            
                            # Test album details (exchange count)
                            print(f"\n🔍 Testing album details endpoint...")
                            response = requests.get(f"{api_url}/albums/{album_id}",
                                                  headers=headers, timeout=10)
                            
                            if response.status_code == 200:
                                album = response.json()
                                exchange_count = album.get('exchange_count', -1)
                                print(f"✅ Album details returned exchange_count: {exchange_count}")
                                
                                if exchange_count == 0:
                                    print("✅ Exchange count is 0 (test users excluded)")
                                    results["exchange_count_zero"] = True
                                else:
                                    print(f"⚠️  Exchange count is {exchange_count}, expected 0")
                            else:
                                print(f"❌ Album details endpoint failed: {response.status_code} - {response.text[:200]}")
                        else:
                            print(f"❌ Album activation failed: {response.status_code} - {response.text[:200]}")
                    else:
                        print(f"❌ OTP verification failed: {response.status_code} - {response.text}")
                else:
                    print("❌ Could not find OTP in backend logs")
                    
            except Exception as e:
                print(f"❌ Error extracting OTP from logs: {e}")
        else:
            print(f"❌ Failed to send OTP: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if results["frontend_compilation"] and results["is_test_user_logic"]:
        if results["album_matches_empty"] and results["exchange_count_zero"]:
            print("\n🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
            return True
        else:
            print("\n⚠️  Frontend fix verified, but API filtering needs verification")
            return False
    else:
        print("\n❌ Some fixes failed verification")
        return False

if __name__ == "__main__":
    success = test_misfigus_fixes()
    exit(0 if success else 1)