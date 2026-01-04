from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import json
import re

from models import (
    User, UserCreate, UserUpdate, OTPVerify, 
    Album, Group, GroupMember, GroupCreate,
    EmailInvite, EmailInviteCreate, EmailInviteAccept,
    Sticker, UserInventory, InventoryUpdate,
    Offer, OfferCreate, OfferUpdate, OfferItem,
    Chat, ChatMessage
)
from email_service import (
    generate_otp_code, generate_invite_code, hash_otp, verify_otp_hash,
    send_otp_email, send_invite_email, check_resend_config
)
from auth import create_token, get_current_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ============================================
# ENVIRONMENT FLAGS
# ============================================
DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'
# DEV_OTP_MODE is REMOVED - OTP should NEVER be shown in UI

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OTP storage (in production, use Redis with TTL)
OTP_STORE = {}  # {email: {hash: str, expires: datetime}}

# Check email service configuration on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting MisFigus API server...")
    check_resend_config()
    logger.info("Server startup complete")

# ============================================
# HELPER: Validate group membership
# ============================================
async def validate_group_member(group_id: str, user_id: str) -> dict:
    """
    Validate that user is an active member of the group.
    Returns group data if valid, raises HTTPException otherwise.
    """
    group = await db.groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    membership = await db.group_members.find_one(
        {"group_id": group_id, "user_id": user_id},
        {"_id": 0}
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    return group

# ============================================
# HELPER: Get group members (excluding owner)
# ============================================
async def get_group_members_excluding_user(group_id: str, exclude_user_id: str) -> tuple:
    """
    Returns (members_list, member_count) excluding specified user.
    """
    other_memberships = await db.group_members.find(
        {"group_id": group_id, "user_id": {"$ne": exclude_user_id}},
        {"_id": 0}
    ).to_list(100)
    
    other_user_ids = [m['user_id'] for m in other_memberships]
    
    if not other_user_ids:
        return [], 0
    
    other_users = await db.users.find(
        {"id": {"$in": other_user_ids}},
        {"_id": 0}
    ).to_list(100)
    
    return other_users, len(other_users)

# ============================================
# AUTH ENDPOINTS (OTP never shown in UI)
# ============================================
@api_router.post("/auth/send-otp")
async def send_otp(user_input: UserCreate):
    """
    Send OTP via email. OTP is NEVER returned in response.
    """
    otp = generate_otp_code()
    otp_hash = hash_otp(otp)
    
    # Store hashed OTP with expiry
    OTP_STORE[user_input.email.lower()] = {
        "hash": otp_hash,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    
    # Create user if doesn't exist
    user = await db.users.find_one({"email": user_input.email}, {"_id": 0})
    if not user:
        new_user = User(email=user_input.email, full_name=user_input.email.split('@')[0], verified=False)
        doc = new_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
    
    # Send OTP via email (logged to console if Resend not configured)
    send_otp_email(user_input.email, otp)
    
    # NEVER return OTP in response
    return {"message": "OTP sent", "email": user_input.email}

@api_router.post("/auth/verify-otp")
async def verify_otp_endpoint(otp_data: OTPVerify):
    """
    Verify OTP code. Validates against stored hash.
    """
    email_lower = otp_data.email.lower()
    stored = OTP_STORE.get(email_lower)
    
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP requested for this email")
    
    if datetime.now(timezone.utc) > stored['expires']:
        del OTP_STORE[email_lower]
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if not verify_otp_hash(otp_data.otp, stored['hash']):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear used OTP
    del OTP_STORE[email_lower]
    
    user = await db.users.find_one({"email": otp_data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"email": otp_data.email},
        {"$set": {"verified": True}}
    )
    
    token = create_token(user['id'])
    return {"token": token, "user": user}

@api_router.get("/auth/me")
async def get_me(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.patch("/auth/me")
async def update_me(user_update: UserUpdate, user_id: str = Depends(get_current_user)):
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user

# ============================================
# ALBUM ENDPOINTS (album templates)
# ============================================
@api_router.get("/albums")
async def get_albums(user_id: str = Depends(get_current_user)):
    """
    Get all album templates (catalog) with user-specific state.
    
    user_state logic:
    - 'coming_soon': album.status == 'coming_soon' (not activatable)
    - 'active': user has activated this album
    - 'inactive': available but user hasn't activated yet
    """
    all_albums = await db.albums.find({}, {"_id": 0}).to_list(100)
    
    # Get user's activated albums
    user_activations = await db.user_album_activations.find(
        {"user_id": user_id}, 
        {"_id": 0, "album_id": 1}
    ).to_list(100)
    activated_album_ids = {a['album_id'] for a in user_activations}
    
    # Compute user_state for each album
    for album in all_albums:
        if album.get('status') == 'coming_soon':
            album['user_state'] = 'coming_soon'
        elif album['id'] in activated_album_ids:
            album['user_state'] = 'active'
            album['is_member'] = True
            # Get member count for active albums
            member_count = await db.album_members.count_documents({"album_id": album['id']})
            # Exclude current user from count
            album['member_count'] = max(0, member_count - 1)
            # Calculate progress
            sticker_count = await db.stickers.count_documents({"album_id": album['id']})
            if sticker_count > 0:
                inventory_count = await db.user_inventory.count_documents({
                    "user_id": user_id,
                    "album_id": album['id'],
                    "owned_qty": {"$gte": 1}
                })
                album['progress'] = round((inventory_count / sticker_count * 100), 1)
            else:
                album['progress'] = 0
        else:
            album['user_state'] = 'inactive'
            album['is_member'] = False
    
    return all_albums

@api_router.post("/albums/{album_id}/activate")
async def activate_album(album_id: str, user_id: str = Depends(get_current_user)):
    """
    Activate an album for the user.
    Creates activation record and adds user as album member.
    """
    # Check album exists and is available
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if album.get('status') == 'coming_soon':
        raise HTTPException(status_code=400, detail="Album not available yet")
    
    # Check if already activated
    existing = await db.user_album_activations.find_one({
        "user_id": user_id,
        "album_id": album_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Album already activated")
    
    # Create activation record
    activation = {
        "user_id": user_id,
        "album_id": album_id,
        "activated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_album_activations.insert_one(activation)
    
    # Add user as album member
    member = {
        "album_id": album_id,
        "user_id": user_id,
        "invited_by_user_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.album_members.insert_one(member)
    
    return {"message": "Album activated", "album_id": album_id}

# ============================================
# GROUP ENDPOINTS (private album instances)
# ============================================
@api_router.get("/groups")
async def get_my_groups(user_id: str = Depends(get_current_user)):
    """
    Get all groups the user is a member of.
    """
    memberships = await db.group_members.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    group_ids = [m['group_id'] for m in memberships]
    
    if not group_ids:
        return []
    
    groups = await db.groups.find({"id": {"$in": group_ids}}, {"_id": 0}).to_list(100)
    
    # Enrich with album info and member count
    for group in groups:
        album_id = group.get('album_id')
        if album_id:
            album = await db.albums.find_one({"id": album_id}, {"_id": 0})
            group['album'] = album
        else:
            group['album'] = None
        
        # Get member count excluding current user
        _, member_count = await get_group_members_excluding_user(group['id'], user_id)
        group['member_count'] = member_count
        
        # Check if user is owner
        group['is_owner'] = (group.get('owner_id') == user_id)
        
        # Calculate progress
        if album_id:
            sticker_count = await db.stickers.count_documents({"album_id": album_id})
            if sticker_count > 0:
                inventory_count = await db.user_inventory.count_documents({
                    "user_id": user_id,
                    "group_id": group['id'],
                    "owned_qty": {"$gte": 1}
                })
                group['progress'] = round((inventory_count / sticker_count * 100), 1)
            else:
                group['progress'] = 0
        else:
            group['progress'] = 0
    
    return groups

@api_router.post("/groups")
async def create_group(group_input: GroupCreate, user_id: str = Depends(get_current_user)):
    """
    Create a new private group for an album.
    User becomes the owner and first member.
    """
    # Verify album exists
    album = await db.albums.find_one({"id": group_input.album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if album.get('status') != 'active':
        raise HTTPException(status_code=400, detail="Album is not available")
    
    # Create group
    group = Group(
        album_id=group_input.album_id,
        name=group_input.name,
        owner_id=user_id
    )
    group_doc = group.model_dump()
    group_doc['created_at'] = group_doc['created_at'].isoformat()
    await db.groups.insert_one(group_doc)
    
    # Add owner as first member
    member = GroupMember(
        group_id=group.id,
        user_id=user_id,
        invited_by_user_id=None
    )
    member_doc = member.model_dump()
    member_doc['joined_at'] = member_doc['joined_at'].isoformat()
    await db.group_members.insert_one(member_doc)
    
    # Remove _id before returning (MongoDB adds it after insert)
    group_doc.pop('_id', None)
    return {"message": "Group created", "group": group_doc}

@api_router.get("/groups/{group_id}")
async def get_group(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Get group details. User must be a member.
    """
    group = await validate_group_member(group_id, user_id)
    
    # Enrich with album info
    album = await db.albums.find_one({"id": group['album_id']}, {"_id": 0})
    group['album'] = album
    
    # Get members excluding current user
    members, member_count = await get_group_members_excluding_user(group_id, user_id)
    group['members'] = members
    group['member_count'] = member_count
    group['is_owner'] = (group['owner_id'] == user_id)
    
    return group

@api_router.delete("/groups/{group_id}/leave")
async def leave_group(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Leave a group. Owner cannot leave (must transfer ownership first).
    """
    group = await validate_group_member(group_id, user_id)
    
    if group['owner_id'] == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot leave the group")
    
    await db.group_members.delete_one({"group_id": group_id, "user_id": user_id})
    return {"message": "Left group successfully"}

# ============================================
# EMAIL INVITE ENDPOINTS
# ============================================
@api_router.post("/groups/{group_id}/invite")
async def create_email_invite(group_id: str, invite_input: EmailInviteCreate, user_id: str = Depends(get_current_user)):
    """
    Send email invite to join group. Any member can invite.
    Code is sent via email only - NEVER returned in response.
    """
    # Validate membership
    group = await validate_group_member(group_id, user_id)
    
    # Check if email is already a member
    existing_user = await db.users.find_one({"email": invite_input.email.lower()}, {"_id": 0})
    if existing_user:
        existing_member = await db.group_members.find_one(
            {"group_id": group_id, "user_id": existing_user['id']},
            {"_id": 0}
        )
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member")
    
    # Check for existing unexpired invite
    existing_invite = await db.email_invites.find_one({
        "group_id": group_id,
        "invited_email": invite_input.email.lower(),
        "used_at": None,
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    }, {"_id": 0})
    
    if existing_invite:
        raise HTTPException(status_code=400, detail="Active invite already exists for this email")
    
    # Generate invite code
    invite_code = generate_invite_code()
    
    # Create invite record
    invite = EmailInvite(
        group_id=group_id,
        invited_email=invite_input.email.lower(),
        invite_code=invite_code,
        created_by_user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    invite_doc = invite.model_dump()
    invite_doc['expires_at'] = invite_doc['expires_at'].isoformat()
    invite_doc['created_at'] = invite_doc['created_at'].isoformat()
    await db.email_invites.insert_one(invite_doc)
    
    # Get inviter info
    inviter = await db.users.find_one({"id": user_id}, {"_id": 0})
    inviter_name = inviter.get('display_name') or inviter.get('full_name') or inviter['email']
    
    # Get album info for group name
    album = await db.albums.find_one({"id": group['album_id']}, {"_id": 0})
    group_display_name = f"{group['name']} ({album['name']})"
    
    # Send invite via email (logged to console if Resend not configured)
    send_invite_email(invite_input.email, invite_code, group_display_name, inviter_name)
    
    # NEVER return invite code in response
    return {
        "message": "Invite sent",
        "invited_email": invite_input.email,
        "expires_in_hours": 1
    }

@api_router.post("/invites/accept")
async def accept_email_invite(invite_data: EmailInviteAccept, user_id: str = Depends(get_current_user)):
    """
    Accept an email invite using the 6-digit code.
    Code must match, not be expired, and not be used.
    User's email must match the invited email.
    """
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find invite by code
    invite = await db.email_invites.find_one(
        {"invite_code": invite_data.invite_code},
        {"_id": 0}
    )
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # Check if already used
    if invite.get('used_at'):
        raise HTTPException(status_code=400, detail="Invite already used")
    
    # Check expiry
    expires_at = datetime.fromisoformat(invite['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="INVITE_EXPIRED")
    
    # Check email matches
    if user['email'].lower() != invite['invited_email'].lower():
        raise HTTPException(status_code=403, detail="Invite was sent to a different email")
    
    # Check not already a member
    existing_member = await db.group_members.find_one(
        {"group_id": invite['group_id'], "user_id": user_id},
        {"_id": 0}
    )
    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member of this group")
    
    # Add user to group
    member = GroupMember(
        group_id=invite['group_id'],
        user_id=user_id,
        invited_by_user_id=invite['created_by_user_id']
    )
    member_doc = member.model_dump()
    member_doc['joined_at'] = member_doc['joined_at'].isoformat()
    await db.group_members.insert_one(member_doc)
    
    # Mark invite as used
    await db.email_invites.update_one(
        {"id": invite['id']},
        {"$set": {"used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Get group info
    group = await db.groups.find_one({"id": invite['group_id']}, {"_id": 0})
    
    return {"message": "Joined group successfully", "group_id": invite['group_id'], "group_name": group['name']}

@api_router.get("/invites/pending")
async def get_pending_invites(user_id: str = Depends(get_current_user)):
    """
    Get pending invites for the current user's email.
    """
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    invites = await db.email_invites.find({
        "invited_email": user['email'].lower(),
        "used_at": None,
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    }, {"_id": 0}).to_list(100)
    
    # Enrich with group/album info (don't expose the code)
    for invite in invites:
        group = await db.groups.find_one({"id": invite['group_id']}, {"_id": 0})
        if group:
            album = await db.albums.find_one({"id": group['album_id']}, {"_id": 0})
            invite['group_name'] = group['name']
            invite['album_name'] = album['name'] if album else None
        # Remove code from response
        invite.pop('invite_code', None)
    
    return invites

# ============================================
# STICKER ENDPOINTS (scoped by group)
# ============================================
@api_router.get("/groups/{group_id}/stickers")
async def get_stickers(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Get stickers for a group's album. User must be a member.
    """
    group = await validate_group_member(group_id, user_id)
    stickers = await db.stickers.find({"album_id": group['album_id']}, {"_id": 0}).to_list(1000)
    return stickers

# ============================================
# INVENTORY ENDPOINTS (scoped by group)
# ============================================
@api_router.get("/groups/{group_id}/inventory")
async def get_inventory(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Get user's inventory for a group. User must be a member.
    """
    group = await validate_group_member(group_id, user_id)
    
    stickers = await db.stickers.find({"album_id": group['album_id']}, {"_id": 0}).to_list(1000)
    
    inventory_items = await db.user_inventory.find({
        "user_id": user_id,
        "group_id": group_id
    }, {"_id": 0}).to_list(1000)
    
    inventory_map = {item['sticker_id']: item['owned_qty'] for item in inventory_items}
    
    for sticker in stickers:
        owned_qty = inventory_map.get(sticker['id'], 0)
        sticker['owned_qty'] = owned_qty
        sticker['duplicate_count'] = max(owned_qty - 1, 0)
    
    return stickers

@api_router.put("/groups/{group_id}/inventory")
async def update_inventory(group_id: str, update: InventoryUpdate, user_id: str = Depends(get_current_user)):
    """
    Update user's inventory for a group. User must be a member.
    """
    await validate_group_member(group_id, user_id)
    
    existing = await db.user_inventory.find_one({
        "user_id": user_id,
        "group_id": group_id,
        "sticker_id": update.sticker_id
    }, {"_id": 0})
    
    if existing:
        await db.user_inventory.update_one(
            {"user_id": user_id, "group_id": group_id, "sticker_id": update.sticker_id},
            {"$set": {"owned_qty": update.owned_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        inventory = UserInventory(
            user_id=user_id,
            group_id=group_id,
            sticker_id=update.sticker_id,
            owned_qty=update.owned_qty
        )
        doc = inventory.model_dump()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.user_inventory.insert_one(doc)
    
    return {"message": "Inventory updated"}

# ============================================
# MATCHES ENDPOINTS (scoped by group)
# ============================================
@api_router.get("/groups/{group_id}/matches")
async def get_matches(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Get potential exchange matches within the group.
    Users from different groups NEVER see each other.
    """
    group = await validate_group_member(group_id, user_id)
    
    stickers = await db.stickers.find({"album_id": group['album_id']}, {"_id": 0}).to_list(1000)
    sticker_ids = [s['id'] for s in stickers]
    
    my_inventory = await db.user_inventory.find({
        "user_id": user_id,
        "group_id": group_id
    }, {"_id": 0}).to_list(1000)
    
    my_inv_map = {item['sticker_id']: item['owned_qty'] for item in my_inventory}
    
    # Get other members (ONLY from this group)
    members, _ = await get_group_members_excluding_user(group_id, user_id)
    
    matches = []
    
    for member in members:
        other_user_id = member['id']
        
        other_inventory = await db.user_inventory.find({
            "user_id": other_user_id,
            "group_id": group_id  # IMPORTANT: Same group only
        }, {"_id": 0}).to_list(1000)
        
        other_inv_map = {item['sticker_id']: item['owned_qty'] for item in other_inventory}
        
        # Calculate what can be exchanged (but don't expose numbers in response)
        my_duplicates = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) >= 2]
        my_missing = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) == 0]
        other_duplicates = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) >= 2]
        other_missing = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) == 0]
        
        i_can_give = [sid for sid in my_duplicates if sid in other_missing]
        i_can_get = [sid for sid in other_duplicates if sid in my_missing]
        
        if i_can_give or i_can_get:
            matches.append({
                "user": {
                    "id": member['id'],
                    "email": member['email'],
                    "display_name": member.get('display_name'),
                    "full_name": member.get('full_name')
                },
                "has_stickers_i_need": len(i_can_get) > 0,
                "needs_stickers_i_have": len(i_can_give) > 0,
                "can_exchange": len(i_can_give) > 0 and len(i_can_get) > 0
            })
    
    return matches

# ============================================
# DEV ENDPOINTS (only when DEV_MODE=true)
# ============================================
if DEV_MODE:
    @api_router.get("/dev/status")
    async def dev_status():
        return {
            "DEV_MODE": DEV_MODE,
            "message": "Dev endpoints enabled"
        }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
