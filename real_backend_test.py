import requests
import sys
import json
from datetime import datetime

def test_real_auth_flow():
    """Test with real OTP from logs"""
    base_url = "https://translate-profile.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔐 Testing Real Authentication Flow")
    print("="*50)
    
    # Step 1: Send OTP
    test_email = f"realtest_{datetime.now().strftime('%H%M%S')}@example.com"
    
    try:
        response = requests.post(f"{api_url}/auth/send-otp", 
                               json={"email": test_email},
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            print(f"✅ OTP sent to: {test_email}")
            print(f"📧 Check logs for OTP: tail -n 5 /var/log/supervisor/backend.err.log | grep 'OTP Code'")
            
            # Wait a moment for log to be written
            import time
            time.sleep(1)
            
            # Get the OTP from logs
            import subprocess
            result = subprocess.run(['tail', '-n', '10', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True)
            
            otp_code = None
            for line in result.stdout.split('\n'):
                if 'OTP Code:' in line:
                    otp_code = line.split('OTP Code:')[1].strip()
                    break
            
            if otp_code:
                print(f"🔑 Found OTP: {otp_code}")
                
                # Step 2: Verify OTP
                verify_response = requests.post(f"{api_url}/auth/verify-otp",
                                              json={"email": test_email, "otp": otp_code},
                                              headers={'Content-Type': 'application/json'},
                                              timeout=10)
                
                if verify_response.status_code == 200:
                    auth_data = verify_response.json()
                    token = auth_data.get('token')
                    user = auth_data.get('user')
                    
                    print(f"✅ Authentication successful!")
                    print(f"   Token: {token[:20]}...")
                    print(f"   User ID: {user.get('id')}")
                    print(f"   Email: {user.get('email')}")
                    
                    # Step 3: Test authenticated endpoint
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {token}'
                    }
                    
                    me_response = requests.get(f"{api_url}/auth/me", headers=headers, timeout=10)
                    if me_response.status_code == 200:
                        print(f"✅ /auth/me endpoint working")
                        return token, user.get('id')
                    else:
                        print(f"❌ /auth/me failed: {me_response.status_code}")
                        
                else:
                    print(f"❌ OTP verification failed: {verify_response.status_code}")
                    print(f"   Response: {verify_response.text}")
            else:
                print(f"❌ Could not find OTP in logs")
                
        else:
            print(f"❌ Send OTP failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during auth test: {e}")
    
    return None, None

def test_full_workflow_with_auth(token, user_id):
    """Test full workflow with valid authentication"""
    if not token:
        print("⚠️  Skipping authenticated tests - no valid token")
        return
        
    base_url = "https://translate-profile.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print(f"\n🏗️  Testing Full Workflow with Authentication")
    print("="*50)
    
    try:
        # Test 1: Get Groups
        groups_response = requests.get(f"{api_url}/groups", headers=headers, timeout=10)
        if groups_response.status_code == 200:
            groups = groups_response.json()
            print(f"✅ Get Groups: Found {len(groups)} groups")
        else:
            print(f"❌ Get Groups failed: {groups_response.status_code}")
            return
        
        # Test 2: Create Group
        group_data = {"name": f"Test Group {datetime.now().strftime('%H%M%S')}"}
        create_response = requests.post(f"{api_url}/groups", 
                                      json=group_data, 
                                      headers=headers, 
                                      timeout=10)
        
        if create_response.status_code == 200:
            new_group = create_response.json()
            group_id = new_group.get('id')
            print(f"✅ Create Group: {new_group.get('name')} (ID: {group_id})")
            
            # Test 3: Get Group Details
            group_detail_response = requests.get(f"{api_url}/groups/{group_id}", 
                                                headers=headers, 
                                                timeout=10)
            if group_detail_response.status_code == 200:
                group_details = group_detail_response.json()
                print(f"✅ Get Group Details: {group_details.get('member_count')} members")
            else:
                print(f"❌ Get Group Details failed: {group_detail_response.status_code}")
            
            # Test 4: Get Albums
            albums_response = requests.get(f"{api_url}/albums?group_id={group_id}", 
                                         headers=headers, 
                                         timeout=10)
            if albums_response.status_code == 200:
                albums = albums_response.json()
                print(f"✅ Get Albums: Found {len(albums)} albums")
                
                if albums:
                    album_id = albums[0].get('id')
                    
                    # Test 5: Get Stickers
                    stickers_response = requests.get(f"{api_url}/albums/{album_id}/stickers", 
                                                   headers=headers, 
                                                   timeout=10)
                    if stickers_response.status_code == 200:
                        stickers = stickers_response.json()
                        print(f"✅ Get Stickers: Found {len(stickers)} stickers")
                        
                        # Test 6: Get Inventory
                        inventory_response = requests.get(f"{api_url}/inventory?album_id={album_id}", 
                                                        headers=headers, 
                                                        timeout=10)
                        if inventory_response.status_code == 200:
                            inventory = inventory_response.json()
                            print(f"✅ Get Inventory: {len(inventory)} items")
                            
                            # Test 7: Update Inventory
                            if stickers:
                                sticker_id = stickers[0].get('id')
                                update_data = {"sticker_id": sticker_id, "owned_qty": 3}
                                update_response = requests.put(f"{api_url}/inventory", 
                                                             json=update_data, 
                                                             headers=headers, 
                                                             timeout=10)
                                if update_response.status_code == 200:
                                    print(f"✅ Update Inventory: Set sticker quantity to 3")
                                else:
                                    print(f"❌ Update Inventory failed: {update_response.status_code}")
                            
                            # Test 8: Get Matches
                            matches_response = requests.get(f"{api_url}/matches?group_id={group_id}&album_id={album_id}", 
                                                          headers=headers, 
                                                          timeout=10)
                            if matches_response.status_code == 200:
                                matches = matches_response.json()
                                print(f"✅ Get Matches: Found {len(matches)} matches")
                            else:
                                print(f"❌ Get Matches failed: {matches_response.status_code}")
                            
                            # Test 9: Get Offers
                            offers_response = requests.get(f"{api_url}/offers?group_id={group_id}", 
                                                         headers=headers, 
                                                         timeout=10)
                            if offers_response.status_code == 200:
                                offers = offers_response.json()
                                print(f"✅ Get Offers: {len(offers.get('sent', []))} sent, {len(offers.get('received', []))} received")
                            else:
                                print(f"❌ Get Offers failed: {offers_response.status_code}")
                            
                            # Test 10: Get Chat Threads
                            chat_response = requests.get(f"{api_url}/chat/threads?group_id={group_id}", 
                                                       headers=headers, 
                                                       timeout=10)
                            if chat_response.status_code == 200:
                                threads = chat_response.json()
                                print(f"✅ Get Chat Threads: Found {len(threads)} threads")
                            else:
                                print(f"❌ Get Chat Threads failed: {chat_response.status_code}")
                            
                            # Test 11: Create Invite
                            invite_data = {"group_id": group_id, "invited_email": "invite@example.com"}
                            invite_response = requests.post(f"{api_url}/groups/{group_id}/invites", 
                                                          json=invite_data, 
                                                          headers=headers, 
                                                          timeout=10)
                            if invite_response.status_code == 200:
                                invite = invite_response.json()
                                print(f"✅ Create Invite: Token generated")
                            else:
                                print(f"❌ Create Invite failed: {invite_response.status_code}")
                            
                            # Test 12: Get Notifications
                            notif_response = requests.get(f"{api_url}/notifications", 
                                                        headers=headers, 
                                                        timeout=10)
                            if notif_response.status_code == 200:
                                notifications = notif_response.json()
                                print(f"✅ Get Notifications: Found {len(notifications)} notifications")
                            else:
                                print(f"❌ Get Notifications failed: {notif_response.status_code}")
                    
                    else:
                        print(f"❌ Get Stickers failed: {stickers_response.status_code}")
            else:
                print(f"❌ Get Albums failed: {albums_response.status_code}")
        else:
            print(f"❌ Create Group failed: {create_response.status_code}")
            print(f"   Response: {create_response.text}")
            
    except Exception as e:
        print(f"❌ Exception during workflow test: {e}")

def main():
    print("🧪 StickerSwap Comprehensive Backend Testing")
    print("="*60)
    
    # Test authentication flow
    token, user_id = test_real_auth_flow()
    
    # Test full workflow if authentication succeeded
    test_full_workflow_with_auth(token, user_id)
    
    print(f"\n✅ Backend testing completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())