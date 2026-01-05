from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body
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
from uuid import uuid4

from models import (
    User, UserCreate, UserUpdate, OTPVerify, 
    Album, Group, GroupMember, GroupCreate,
    EmailInvite, EmailInviteCreate, EmailInviteAccept,
    Sticker, UserInventory, InventoryUpdate,
    Offer, OfferCreate, OfferUpdate, OfferItem,
    Chat, ChatMessage,
    Exchange, ExchangeCreate, ExchangeConfirm, 
    UserReputation, EXCHANGE_FAILURE_REASONS,
    REPUTATION_CONSECUTIVE_FAIL_THRESHOLD, REPUTATION_TOTAL_FAIL_THRESHOLD
)
from datetime import timedelta
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
# HELPER: Detect test/seed users
# ============================================
def is_test_user(user: dict) -> bool:
    """
    Check if a user is a test/seed user that should be excluded from exchanges.
    Test users are identified by:
    - Email ending with @test.com
    - Email ending with @misfigus.com (internal test domain)
    - Email containing +test (common test pattern)
    - is_test_user flag set to True
    - role set to 'seed'
    """
    if not user:
        return True  # Treat missing users as test users for safety
    
    email = (user.get('email') or '').lower()
    
    # Check email patterns
    if email.endswith('@test.com'):
        return True
    if email.endswith('@misfigus.com'):
        return True
    if '+test' in email:
        return True
    
    # Check flags/role if present
    if user.get('is_test_user') is True:
        return True
    if user.get('role') == 'seed':
        return True
    
    return False

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
            # Get member count for active albums (excluding current user)
            member_count = await db.album_members.count_documents({"album_id": album['id']})
            album['member_count'] = max(0, member_count - 1)  # Exclude current user
            # Calculate progress (rounded to integer - no decimals)
            sticker_count = await db.stickers.count_documents({"album_id": album['id']})
            if sticker_count > 0:
                inventory_count = await db.user_inventory.count_documents({
                    "user_id": user_id,
                    "album_id": album['id'],
                    "owned_qty": {"$gte": 1}
                })
                album['progress'] = round(inventory_count / sticker_count * 100)  # Integer
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

@api_router.delete("/albums/{album_id}/deactivate")
async def deactivate_album(album_id: str, user_id: str = Depends(get_current_user)):
    """
    Deactivate an album for the user.
    Removes activation record but preserves inventory.
    """
    # Check album exists
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Check if user has activated this album
    activation = await db.user_album_activations.find_one({
        "user_id": user_id,
        "album_id": album_id
    })
    
    if not activation:
        raise HTTPException(status_code=400, detail="Album not activated")
    
    # Remove activation record (but keep inventory for future reactivation)
    await db.user_album_activations.delete_one({
        "user_id": user_id,
        "album_id": album_id
    })
    
    # Remove user from album members
    await db.album_members.delete_one({
        "user_id": user_id,
        "album_id": album_id
    })
    
    return {"message": "Album deactivated", "album_id": album_id}

@api_router.get("/albums/{album_id}")
async def get_album(album_id: str, user_id: str = Depends(get_current_user)):
    """Get album template details with progress and exchange count."""
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Check if user has activated this album
    activation = await db.user_album_activations.find_one({
        "user_id": user_id,
        "album_id": album_id
    })
    
    if album.get('status') == 'coming_soon':
        album['user_state'] = 'coming_soon'
        album['is_member'] = False
        album['progress'] = 0
        album['exchange_count'] = 0
    elif activation:
        album['user_state'] = 'active'
        album['is_member'] = True
        
        # Calculate progress (rounded to integer)
        sticker_count = await db.stickers.count_documents({"album_id": album_id})
        if sticker_count > 0:
            inventory_count = await db.user_inventory.count_documents({
                "user_id": user_id,
                "album_id": album_id,
                "owned_qty": {"$gte": 1}
            })
            album['progress'] = round(inventory_count / sticker_count * 100)
        else:
            album['progress'] = 0
        
        # Calculate exchange count (users with mutual matches in this album)
        album['exchange_count'] = await compute_album_exchange_count(album_id, user_id)
    else:
        album['user_state'] = 'inactive'
        album['is_member'] = False
        album['progress'] = 0
        album['exchange_count'] = 0
    
    return album

async def compute_album_exchange_count(album_id: str, user_id: str) -> int:
    """
    Compute count of potential exchange partners for this album.
    A match exists when: I have duplicates they need AND they have duplicates I need.
    This is LOCAL exchanges only (based on album membership, not geographic radius yet).
    Returns count only, not user details (privacy-preserving).
    EXCLUDES test/seed users from the count.
    """
    # Get all stickers for this album
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0, "id": 1}).to_list(1000)
    sticker_ids = [s['id'] for s in stickers]
    
    if not sticker_ids:
        return 0
    
    # Get my inventory
    my_inventory = await db.user_inventory.find({
        "user_id": user_id,
        "album_id": album_id
    }, {"_id": 0}).to_list(1000)
    
    my_inv_map = {item['sticker_id']: item['owned_qty'] for item in my_inventory}
    
    # My duplicates (owned >= 2) and missing (owned == 0)
    my_duplicates = set(sid for sid in sticker_ids if my_inv_map.get(sid, 0) >= 2)
    my_missing = set(sid for sid in sticker_ids if my_inv_map.get(sid, 0) == 0)
    
    # If user has no duplicates or no missing, no exchanges possible
    if not my_duplicates or not my_missing:
        return 0
    
    # Get other album members
    other_members = await db.album_members.find(
        {"album_id": album_id, "user_id": {"$ne": user_id}},
        {"_id": 0, "user_id": 1}
    ).to_list(1000)
    
    exchange_count = 0
    
    for member in other_members:
        other_user_id = member['user_id']
        
        # Get user info and skip test/seed users
        other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
        if is_test_user(other_user):
            continue  # Skip test/seed users
        
        # Get their inventory
        other_inventory = await db.user_inventory.find({
            "user_id": other_user_id,
            "album_id": album_id
        }, {"_id": 0}).to_list(1000)
        
        other_inv_map = {item['sticker_id']: item['owned_qty'] for item in other_inventory}
        
        # Their duplicates and missing
        other_duplicates = set(sid for sid in sticker_ids if other_inv_map.get(sid, 0) >= 2)
        other_missing = set(sid for sid in sticker_ids if other_inv_map.get(sid, 0) == 0)
        
        # Mutual match: I can give them something AND they can give me something
        i_can_give = my_duplicates & other_missing
        i_can_get = other_duplicates & my_missing
        
        # Only count if MUTUAL exchange is possible (both directions)
        if i_can_give and i_can_get:
            exchange_count += 1
    
    return exchange_count

@api_router.get("/albums/{album_id}/matches")
async def get_album_matches(album_id: str, user_id: str = Depends(get_current_user)):
    """
    Get potential exchange matches within the album.
    Only returns users with MUTUAL matches (both can exchange).
    Does not expose user lists/directories - only real exchange opportunities.
    """
    # Verify user has activated this album
    activation = await db.user_album_activations.find_one({
        "user_id": user_id,
        "album_id": album_id
    })
    if not activation:
        raise HTTPException(status_code=403, detail="Album not activated")
    
    # Get all stickers for this album
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    sticker_ids = [s['id'] for s in stickers]
    
    if not sticker_ids:
        return []
    
    # Get my inventory
    my_inventory = await db.user_inventory.find({
        "user_id": user_id,
        "album_id": album_id
    }, {"_id": 0}).to_list(1000)
    
    my_inv_map = {item['sticker_id']: item['owned_qty'] for item in my_inventory}
    
    my_duplicates = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) >= 2]
    my_missing = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) == 0]
    
    # Get other album members
    other_members = await db.album_members.find(
        {"album_id": album_id, "user_id": {"$ne": user_id}},
        {"_id": 0, "user_id": 1}
    ).to_list(1000)
    
    matches = []
    
    for member in other_members:
        other_user_id = member['user_id']
        
        # Get user info
        other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
        if not other_user:
            continue
        
        # Get their inventory
        other_inventory = await db.user_inventory.find({
            "user_id": other_user_id,
            "album_id": album_id
        }, {"_id": 0}).to_list(1000)
        
        other_inv_map = {item['sticker_id']: item['owned_qty'] for item in other_inventory}
        
        other_duplicates = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) >= 2]
        other_missing = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) == 0]
        
        i_can_give = [sid for sid in my_duplicates if sid in other_missing]
        i_can_get = [sid for sid in other_duplicates if sid in my_missing]
        
        # Only include MUTUAL matches (both directions)
        if i_can_give and i_can_get:
            matches.append({
                "user": {
                    "id": other_user['id'],
                    "email": other_user.get('email'),
                    "display_name": other_user.get('display_name')
                },
                "has_stickers_i_need": len(i_can_get) > 0,
                "needs_stickers_i_have": len(i_can_give) > 0,
                "can_exchange": True  # Only true matches are included
            })
    
    return matches

@api_router.get("/inventory")
async def get_inventory(album_id: str, user_id: str = Depends(get_current_user)):
    """
    Get full sticker catalog for an album with user's ownership overlay.
    Returns ALL stickers in the album, with owned_qty for user's inventory.
    """
    # Check album exists
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Get all stickers for this album (full catalog from database)
    stickers = await db.stickers.find(
        {"album_id": album_id}, 
        {"_id": 0}
    ).sort("number", 1).to_list(1000)
    
    # Get user's inventory for this album
    user_inventory = await db.user_inventory.find(
        {"user_id": user_id, "album_id": album_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Create lookup dict for user's owned quantities
    inventory_map = {inv['sticker_id']: inv['owned_qty'] for inv in user_inventory}
    
    # Merge catalog with user's ownership
    for sticker in stickers:
        owned_qty = inventory_map.get(sticker['id'], 0)
        sticker['owned_qty'] = owned_qty
        sticker['duplicate_count'] = max(0, owned_qty - 1)
    
    return stickers

@api_router.put("/inventory")
async def update_inventory(
    sticker_id: str = Body(...),
    owned_qty: int = Body(...),
    user_id: str = Depends(get_current_user)
):
    """Update user's inventory for a specific sticker."""
    # Get sticker to find album_id
    sticker = await db.stickers.find_one({"id": sticker_id}, {"_id": 0})
    if not sticker:
        raise HTTPException(status_code=404, detail="Sticker not found")
    
    album_id = sticker['album_id']
    
    # Upsert inventory record
    await db.user_inventory.update_one(
        {"user_id": user_id, "sticker_id": sticker_id, "album_id": album_id},
        {"$set": {"owned_qty": max(0, owned_qty)}},
        upsert=True
    )
    
    return {"message": "Inventory updated"}

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
# EXCHANGE ENDPOINTS (Real Exchange Lifecycle)
# ============================================

EXCHANGE_EXPIRY_DAYS = 7  # Exchanges expire after 7 days

async def get_user_reputation(user_id: str) -> dict:
    """Get or create user reputation record."""
    rep = await db.user_reputation.find_one({"user_id": user_id}, {"_id": 0})
    if not rep:
        rep = {
            "user_id": user_id,
            "total_exchanges": 0,
            "successful_exchanges": 0,
            "failed_exchanges": 0,
            "consecutive_failures": 0,
            "status": "trusted",
            "invisible_until": None,
            "suspended_at": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.user_reputation.insert_one(rep)
    return rep

async def update_reputation_after_exchange(user_id: str, was_successful: bool):
    """Update user reputation after an exchange confirmation."""
    rep = await get_user_reputation(user_id)
    
    rep['total_exchanges'] += 1
    
    if was_successful:
        rep['successful_exchanges'] += 1
        rep['consecutive_failures'] = 0  # Reset consecutive failures
    else:
        rep['failed_exchanges'] += 1
        rep['consecutive_failures'] += 1
    
    # Determine new status based on thresholds
    now = datetime.now(timezone.utc)
    
    if rep['consecutive_failures'] >= REPUTATION_CONSECUTIVE_FAIL_THRESHOLD:
        # 2+ consecutive failures → 48h invisibility
        rep['status'] = 'under_review'
        rep['invisible_until'] = (now + timedelta(hours=48)).isoformat()
    
    if rep['failed_exchanges'] >= REPUTATION_TOTAL_FAIL_THRESHOLD:
        # 5+ total failures → suspended
        rep['status'] = 'restricted'
        rep['suspended_at'] = now.isoformat()
    
    # If no issues and was successful, ensure trusted status
    if was_successful and rep['consecutive_failures'] == 0 and rep['status'] == 'under_review':
        # Check if invisibility period has passed
        if rep['invisible_until']:
            inv_until = datetime.fromisoformat(rep['invisible_until'].replace('Z', '+00:00'))
            if now > inv_until:
                rep['status'] = 'trusted'
                rep['invisible_until'] = None
    
    rep['updated_at'] = now.isoformat()
    
    await db.user_reputation.update_one(
        {"user_id": user_id},
        {"$set": rep},
        upsert=True
    )
    
    return rep

async def is_user_visible(user_id: str) -> bool:
    """Check if user is visible (not restricted or invisible)."""
    rep = await get_user_reputation(user_id)
    
    if rep['status'] == 'restricted':
        return False
    
    if rep['invisible_until']:
        inv_until = datetime.fromisoformat(rep['invisible_until'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) < inv_until:
            return False
    
    return True

@api_router.post("/albums/{album_id}/exchanges")
async def create_exchange(
    album_id: str, 
    exchange_input: ExchangeCreate,
    user_id: str = Depends(get_current_user)
):
    """
    Create an exchange with another user.
    Only allowed if there is a MUTUAL sticker match.
    Creates an exchange record and enables chat between users.
    """
    # Verify user has activated this album
    activation = await db.user_album_activations.find_one({
        "user_id": user_id,
        "album_id": album_id
    })
    if not activation:
        raise HTTPException(status_code=403, detail="Album not activated")
    
    partner_id = exchange_input.partner_user_id
    
    # Check partner exists and has activated the album
    partner_activation = await db.user_album_activations.find_one({
        "user_id": partner_id,
        "album_id": album_id
    })
    if not partner_activation:
        raise HTTPException(status_code=404, detail="Partner not found in this album")
    
    # Check both users are visible (reputation check)
    if not await is_user_visible(user_id):
        raise HTTPException(status_code=403, detail="Your account is currently restricted")
    if not await is_user_visible(partner_id):
        raise HTTPException(status_code=404, detail="Partner not available for exchanges")
    
    # Check for existing pending exchange between these users
    existing = await db.exchanges.find_one({
        "album_id": album_id,
        "status": "pending",
        "$or": [
            {"user_a_id": user_id, "user_b_id": partner_id},
            {"user_a_id": partner_id, "user_b_id": user_id}
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Exchange already exists")
    
    # Verify mutual match exists
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0, "id": 1}).to_list(1000)
    sticker_ids = [s['id'] for s in stickers]
    
    my_inventory = await db.user_inventory.find({
        "user_id": user_id,
        "album_id": album_id
    }, {"_id": 0}).to_list(1000)
    my_inv_map = {item['sticker_id']: item['owned_qty'] for item in my_inventory}
    
    partner_inventory = await db.user_inventory.find({
        "user_id": partner_id,
        "album_id": album_id
    }, {"_id": 0}).to_list(1000)
    partner_inv_map = {item['sticker_id']: item['owned_qty'] for item in partner_inventory}
    
    my_duplicates = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) >= 2]
    my_missing = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) == 0]
    partner_duplicates = [sid for sid in sticker_ids if partner_inv_map.get(sid, 0) >= 2]
    partner_missing = [sid for sid in sticker_ids if partner_inv_map.get(sid, 0) == 0]
    
    i_can_give = [sid for sid in my_duplicates if sid in partner_missing]
    i_can_get = [sid for sid in partner_duplicates if sid in my_missing]
    
    if not i_can_give or not i_can_get:
        raise HTTPException(status_code=400, detail="No mutual match exists")
    
    # Create exchange
    now = datetime.now(timezone.utc)
    exchange = {
        "id": str(uuid4()),
        "album_id": album_id,
        "user_a_id": user_id,
        "user_b_id": partner_id,
        "user_a_offers": i_can_give,
        "user_b_offers": i_can_get,
        "status": "pending",
        "user_a_confirmed": None,
        "user_b_confirmed": None,
        "user_a_confirmed_at": None,
        "user_b_confirmed_at": None,
        "user_a_failure_reason": None,
        "user_b_failure_reason": None,
        "created_at": now.isoformat(),
        "completed_at": None,
        "expires_at": (now + timedelta(days=EXCHANGE_EXPIRY_DAYS)).isoformat()
    }
    await db.exchanges.insert_one(exchange)
    
    # Create chat for this exchange
    chat = {
        "id": str(uuid4()),
        "exchange_id": exchange['id'],
        "user_a_id": user_id,
        "user_b_id": partner_id,
        "created_at": now.isoformat()
    }
    await db.chats.insert_one(chat)
    
    # Add system message
    system_message = {
        "id": str(uuid4()),
        "chat_id": chat['id'],
        "sender_id": "system",
        "content": "Exchange started. Coordinate your in-person exchange here.",
        "is_system": True,
        "created_at": now.isoformat()
    }
    await db.chat_messages.insert_one(system_message)
    
    exchange.pop('_id', None)
    return {"message": "Exchange created", "exchange": exchange}

@api_router.get("/albums/{album_id}/exchanges")
async def get_user_exchanges(album_id: str, user_id: str = Depends(get_current_user)):
    """Get all exchanges for the current user in this album."""
    exchanges = await db.exchanges.find({
        "album_id": album_id,
        "$or": [
            {"user_a_id": user_id},
            {"user_b_id": user_id}
        ]
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with partner info and reputation
    for exchange in exchanges:
        partner_id = exchange['user_b_id'] if exchange['user_a_id'] == user_id else exchange['user_a_id']
        partner = await db.users.find_one({"id": partner_id}, {"_id": 0})
        partner_rep = await get_user_reputation(partner_id)
        
        exchange['partner'] = {
            "id": partner_id,
            "display_name": partner.get('display_name') if partner else None,
            "reputation_status": partner_rep['status']
        }
        
        # Mark which user is "me"
        exchange['is_user_a'] = exchange['user_a_id'] == user_id
    
    return exchanges

@api_router.get("/exchanges/{exchange_id}")
async def get_exchange(exchange_id: str, user_id: str = Depends(get_current_user)):
    """Get exchange details. Only participants can view."""
    exchange = await db.exchanges.find_one({"id": exchange_id}, {"_id": 0})
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    if user_id not in [exchange['user_a_id'], exchange['user_b_id']]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Enrich with partner info
    partner_id = exchange['user_b_id'] if exchange['user_a_id'] == user_id else exchange['user_a_id']
    partner = await db.users.find_one({"id": partner_id}, {"_id": 0})
    partner_rep = await get_user_reputation(partner_id)
    
    exchange['partner'] = {
        "id": partner_id,
        "display_name": partner.get('display_name') if partner else None,
        "reputation_status": partner_rep['status']
    }
    exchange['is_user_a'] = exchange['user_a_id'] == user_id
    
    # Enrich sticker info
    for sticker_list_key in ['user_a_offers', 'user_b_offers']:
        sticker_ids = exchange.get(sticker_list_key, [])
        stickers = await db.stickers.find({"id": {"$in": sticker_ids}}, {"_id": 0}).to_list(100)
        exchange[f'{sticker_list_key}_details'] = stickers
    
    return exchange

@api_router.post("/exchanges/{exchange_id}/confirm")
async def confirm_exchange(
    exchange_id: str, 
    confirmation: ExchangeConfirm,
    user_id: str = Depends(get_current_user)
):
    """
    Confirm an exchange result (👍 or 👎).
    Exchange becomes completed when both confirm 👍.
    Exchange becomes failed if either confirms 👎.
    """
    exchange = await db.exchanges.find_one({"id": exchange_id}, {"_id": 0})
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    if user_id not in [exchange['user_a_id'], exchange['user_b_id']]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if exchange['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Exchange is no longer pending")
    
    # Validate failure reason if 👎
    if not confirmation.confirmed:
        if not confirmation.failure_reason or confirmation.failure_reason not in EXCHANGE_FAILURE_REASONS:
            raise HTTPException(status_code=400, detail=f"Failure reason required. Options: {EXCHANGE_FAILURE_REASONS}")
    
    # Check if user already confirmed
    is_user_a = exchange['user_a_id'] == user_id
    confirmed_field = 'user_a_confirmed' if is_user_a else 'user_b_confirmed'
    
    if exchange[confirmed_field] is not None:
        raise HTTPException(status_code=400, detail="Already confirmed")
    
    now = datetime.now(timezone.utc)
    
    # Update confirmation
    update_data = {
        confirmed_field: confirmation.confirmed,
        f'{confirmed_field}_at': now.isoformat()
    }
    
    if not confirmation.confirmed:
        reason_field = 'user_a_failure_reason' if is_user_a else 'user_b_failure_reason'
        update_data[reason_field] = confirmation.failure_reason
    
    await db.exchanges.update_one({"id": exchange_id}, {"$set": update_data})
    
    # Re-fetch to check if both have confirmed
    exchange = await db.exchanges.find_one({"id": exchange_id}, {"_id": 0})
    
    # Determine final status
    final_status = None
    
    if exchange['user_a_confirmed'] is not None and exchange['user_b_confirmed'] is not None:
        # Both have confirmed
        if exchange['user_a_confirmed'] and exchange['user_b_confirmed']:
            final_status = 'completed'
        else:
            final_status = 'failed'
    elif not confirmation.confirmed:
        # One user said 👎 - exchange failed immediately
        final_status = 'failed'
    
    if final_status:
        await db.exchanges.update_one(
            {"id": exchange_id},
            {"$set": {"status": final_status, "completed_at": now.isoformat()}}
        )
        
        # Update reputation for both users
        await update_reputation_after_exchange(
            exchange['user_a_id'], 
            final_status == 'completed'
        )
        await update_reputation_after_exchange(
            exchange['user_b_id'], 
            final_status == 'completed'
        )
        
        # Add system message to chat
        chat = await db.chats.find_one({"exchange_id": exchange_id}, {"_id": 0})
        if chat:
            status_msg = "✅ Exchange completed successfully!" if final_status == 'completed' else "❌ Exchange was not completed."
            system_message = {
                "id": str(uuid4()),
                "chat_id": chat['id'],
                "sender_id": "system",
                "content": status_msg,
                "is_system": True,
                "created_at": now.isoformat()
            }
            await db.chat_messages.insert_one(system_message)
    
    return {"message": "Confirmation recorded", "status": final_status or exchange['status']}

@api_router.get("/user/reputation")
async def get_my_reputation(user_id: str = Depends(get_current_user)):
    """Get current user's reputation status."""
    rep = await get_user_reputation(user_id)
    return rep

# ============================================
# CHAT ENDPOINTS (Only for pending exchanges)
# ============================================

@api_router.get("/exchanges/{exchange_id}/chat")
async def get_exchange_chat(exchange_id: str, user_id: str = Depends(get_current_user)):
    """Get chat for an exchange. Only participants can view."""
    exchange = await db.exchanges.find_one({"id": exchange_id}, {"_id": 0})
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    if user_id not in [exchange['user_a_id'], exchange['user_b_id']]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    chat = await db.chats.find_one({"exchange_id": exchange_id}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = await db.chat_messages.find(
        {"chat_id": chat['id']},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return {
        "chat": chat,
        "messages": messages,
        "is_read_only": exchange['status'] != 'pending'
    }

@api_router.post("/exchanges/{exchange_id}/chat/messages")
async def send_chat_message(
    exchange_id: str,
    content: str = Body(..., embed=True),
    user_id: str = Depends(get_current_user)
):
    """Send a message in an exchange chat. Only allowed for pending exchanges."""
    exchange = await db.exchanges.find_one({"id": exchange_id}, {"_id": 0})
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    if user_id not in [exchange['user_a_id'], exchange['user_b_id']]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if exchange['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Chat is closed for this exchange")
    
    chat = await db.chats.find_one({"exchange_id": exchange_id}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    now = datetime.now(timezone.utc)
    message = {
        "id": str(uuid4()),
        "chat_id": chat['id'],
        "sender_id": user_id,
        "content": content,
        "is_system": False,
        "created_at": now.isoformat()
    }
    await db.chat_messages.insert_one(message)
    
    message.pop('_id', None)
    return message

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
