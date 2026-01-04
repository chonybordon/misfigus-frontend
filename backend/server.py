from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timedelta, timezone
import json

from models import (
    User, UserCreate, UserUpdate, OTPVerify, Album, AlbumMember, Sticker, 
    UserInventory, InventoryUpdate, InviteToken, InviteCreate,
    Offer, OfferCreate, OfferUpdate, OfferItem
)
from auth import (
    generate_otp, send_otp_email, store_otp, verify_otp,
    create_token, get_current_user
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# DEV MODE flag - only show OTP when explicitly enabled
DEV_OTP_MODE = os.environ.get('DEV_OTP_MODE', 'false').lower() == 'true'

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# HELPER: Get other members count (excluding current user)
# ============================================
async def get_other_members_count(album_id: str, current_user_id: str) -> int:
    """Returns count of members EXCLUDING the current user."""
    return await db.album_members.count_documents({
        "album_id": album_id,
        "user_id": {"$ne": current_user_id}
    })

async def get_other_members_list(album_id: str, current_user_id: str) -> list:
    """Returns list of members EXCLUDING the current user."""
    other_memberships = await db.album_members.find({
        "album_id": album_id,
        "user_id": {"$ne": current_user_id}
    }, {"_id": 0}).to_list(100)
    
    other_user_ids = [m['user_id'] for m in other_memberships]
    
    if not other_user_ids:
        return []
    
    other_users = await db.users.find(
        {"id": {"$in": other_user_ids}},
        {"_id": 0}
    ).to_list(100)
    
    return other_users

# ============================================
# AUTH ENDPOINTS
# ============================================
@api_router.post("/auth/send-otp")
async def send_otp(user_input: UserCreate):
    otp = generate_otp()
    store_otp(user_input.email, otp)
    send_otp_email(user_input.email, otp)
    
    user = await db.users.find_one({"email": user_input.email}, {"_id": 0})
    if not user:
        new_user = User(email=user_input.email, full_name=user_input.email.split('@')[0], verified=False)
        doc = new_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
    
    # Only return dev_otp in DEV mode
    response = {"message": "OTP sent", "email": user_input.email}
    if DEV_OTP_MODE:
        response["dev_otp"] = otp
    
    return response

@api_router.post("/auth/verify-otp")
async def verify_otp_endpoint(otp_data: OTPVerify):
    if not verify_otp(otp_data.email, otp_data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
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
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user

# ============================================
# ALBUM ENDPOINTS - Using consistent member counting
# ============================================
@api_router.get("/albums")
async def get_albums(user_id: str = Depends(get_current_user)):
    all_albums = await db.albums.find({}, {"_id": 0}).to_list(100)
    
    # Get user's album activations
    activations = await db.user_album_activations.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    activated_album_ids = [a['album_id'] for a in activations]
    
    # Get user's memberships
    memberships = await db.album_members.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    member_album_ids = [m['album_id'] for m in memberships]
    
    for album in all_albums:
        # Determine state per user
        if album['id'] in activated_album_ids:
            album['user_state'] = 'active'
            album['is_member'] = album['id'] in member_album_ids
        elif album['status'] == 'active':
            album['user_state'] = 'inactive'
            album['is_member'] = False
        else:
            album['user_state'] = 'coming_soon'
            album['is_member'] = False
        
        if album['is_member']:
            # Use helper for consistent counting (EXCLUDING current user)
            album['member_count'] = await get_other_members_count(album['id'], user_id)
            
            sticker_count = await db.stickers.count_documents({"album_id": album['id']})
            inventory_count = await db.user_inventory.count_documents({
                "user_id": user_id,
                "sticker_id": {"$in": [s['id'] async for s in db.stickers.find({"album_id": album['id']}, {"id": 1, "_id": 0})]},
                "owned_qty": {"$gte": 1}
            })
            album['progress'] = round((inventory_count / sticker_count * 100) if sticker_count > 0 else 0, 1)
    
    return all_albums

@api_router.get("/albums/{album_id}")
async def get_album(album_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.album_members.find_one({"album_id": album_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this album")
    
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Use helpers for consistent member list (EXCLUDING current user)
    album['members'] = await get_other_members_list(album_id, user_id)
    album['member_count'] = len(album['members'])
    
    sticker_count = await db.stickers.count_documents({"album_id": album_id})
    inventory_count = await db.user_inventory.count_documents({
        "user_id": user_id,
        "sticker_id": {"$in": [s['id'] async for s in db.stickers.find({"album_id": album_id}, {"id": 1, "_id": 0})]},
        "owned_qty": {"$gte": 1}
    })
    album['progress'] = round((inventory_count / sticker_count * 100) if sticker_count > 0 else 0, 1)
    
    return album

@api_router.post("/albums/{album_id}/invites")
async def create_invite(album_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.album_members.find_one({"album_id": album_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this album")
    
    invite = InviteToken(
        album_id=album_id,
        created_by_user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    doc = invite.model_dump()
    doc['expires_at'] = doc['expires_at'].isoformat()
    await db.invite_tokens.insert_one(doc)
    
    return {"token": invite.token, "expires_at": invite.expires_at}

@api_router.post("/albums/{album_id}/activate")
async def activate_album(album_id: str, user_id: str = Depends(get_current_user)):
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if album['status'] != 'active':
        raise HTTPException(status_code=400, detail="Album cannot be activated")
    
    # Check if already activated
    existing_activation = await db.user_album_activations.find_one({
        "user_id": user_id,
        "album_id": album_id
    }, {"_id": 0})
    
    if existing_activation:
        # Already activated, just ensure membership
        existing_member = await db.album_members.find_one({
            "album_id": album_id,
            "user_id": user_id
        }, {"_id": 0})
        
        if not existing_member:
            member = AlbumMember(
                album_id=album_id,
                user_id=user_id,
                invited_by_user_id=None
            )
            member_doc = member.model_dump()
            member_doc['created_at'] = member_doc['created_at'].isoformat()
            await db.album_members.insert_one(member_doc)
        
        return {"message": "Album already activated"}
    
    # Create activation record
    activation = {
        "user_id": user_id,
        "album_id": album_id,
        "activated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_album_activations.insert_one(activation)
    
    # Auto-create membership
    existing_member = await db.album_members.find_one({
        "album_id": album_id,
        "user_id": user_id
    }, {"_id": 0})
    
    if not existing_member:
        member = AlbumMember(
            album_id=album_id,
            user_id=user_id,
            invited_by_user_id=None
        )
        member_doc = member.model_dump()
        member_doc['created_at'] = member_doc['created_at'].isoformat()
        await db.album_members.insert_one(member_doc)
    
    return {"message": "Album activated successfully"}

@api_router.delete("/albums/{album_id}/deactivate")
async def deactivate_album(album_id: str, user_id: str = Depends(get_current_user)):
    # Remove activation record (inventory is preserved)
    result = await db.user_album_activations.delete_one({
        "user_id": user_id,
        "album_id": album_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Album not activated")
    
    return {"message": "Album deactivated successfully"}

@api_router.post("/albums/{album_id}/join")
async def join_album(album_id: str, user_id: str = Depends(get_current_user)):
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if album['status'] != 'active':
        raise HTTPException(status_code=400, detail="Album is not active")
    
    existing = await db.album_members.find_one({"album_id": album_id, "user_id": user_id}, {"_id": 0})
    if existing:
        return {"message": "Already a member"}
    
    member = AlbumMember(
        album_id=album_id,
        user_id=user_id,
        invited_by_user_id=None
    )
    member_doc = member.model_dump()
    member_doc['created_at'] = member_doc['created_at'].isoformat()
    await db.album_members.insert_one(member_doc)
    
    return {"message": "Joined album successfully"}

@api_router.get("/invites/{token}")
async def get_invite(token: str):
    invite = await db.invite_tokens.find_one({"token": token}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite.get('used_at'):
        raise HTTPException(status_code=400, detail="Invite already used")
    
    expires_at = datetime.fromisoformat(invite['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Invite expired")
    
    album = await db.albums.find_one({"id": invite['album_id']}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    return {"album": album, "invite": invite}

@api_router.post("/invites/{token}/accept")
async def accept_invite(token: str, user_id: str = Depends(get_current_user)):
    invite = await db.invite_tokens.find_one({"token": token}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite.get('used_at'):
        raise HTTPException(status_code=400, detail="Invite already used")
    
    expires_at = datetime.fromisoformat(invite['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Invite expired")
    
    existing = await db.album_members.find_one({"album_id": invite['album_id'], "user_id": user_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")
    
    member = AlbumMember(
        album_id=invite['album_id'],
        user_id=user_id,
        invited_by_user_id=invite['created_by_user_id']
    )
    member_doc = member.model_dump()
    member_doc['created_at'] = member_doc['created_at'].isoformat()
    await db.album_members.insert_one(member_doc)
    
    await db.invite_tokens.update_one(
        {"token": token},
        {"$set": {"used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Joined album successfully"}

@api_router.get("/albums/{album_id}/stickers")
async def get_stickers(album_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.album_members.find_one({"album_id": album_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this album")
    
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    return stickers

@api_router.get("/inventory")
async def get_inventory(album_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.album_members.find_one({"album_id": album_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this album")
    
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    
    inventory_items = await db.user_inventory.find({
        "user_id": user_id,
        "sticker_id": {"$in": [s['id'] for s in stickers]}
    }, {"_id": 0}).to_list(1000)
    
    inventory_map = {item['sticker_id']: item['owned_qty'] for item in inventory_items}
    
    for sticker in stickers:
        owned_qty = inventory_map.get(sticker['id'], 0)
        sticker['owned_qty'] = owned_qty
        sticker['duplicate_count'] = max(owned_qty - 1, 0)
    
    return stickers

@api_router.put("/inventory")
async def update_inventory(update: InventoryUpdate, user_id: str = Depends(get_current_user)):
    existing = await db.user_inventory.find_one({
        "user_id": user_id,
        "sticker_id": update.sticker_id
    }, {"_id": 0})
    
    if existing:
        await db.user_inventory.update_one(
            {"user_id": user_id, "sticker_id": update.sticker_id},
            {"$set": {"owned_qty": update.owned_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        inventory = UserInventory(user_id=user_id, sticker_id=update.sticker_id, owned_qty=update.owned_qty)
        doc = inventory.model_dump()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.user_inventory.insert_one(doc)
    
    return {"message": "Inventory updated"}

@api_router.get("/matches")
async def get_matches(album_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.album_members.find_one({"album_id": album_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this album")
    
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    sticker_ids = [s['id'] for s in stickers]
    sticker_map = {s['id']: s for s in stickers}
    
    my_inventory = await db.user_inventory.find({
        "user_id": user_id,
        "sticker_id": {"$in": sticker_ids}
    }, {"_id": 0}).to_list(1000)
    
    my_inv_map = {item['sticker_id']: item['owned_qty'] for item in my_inventory}
    
    members = await db.album_members.find({"album_id": album_id}, {"_id": 0}).to_list(100)
    other_user_ids = [m['user_id'] for m in members if m['user_id'] != user_id]
    
    matches = []
    
    for other_user_id in other_user_ids:
        other_inventory = await db.user_inventory.find({
            "user_id": other_user_id,
            "sticker_id": {"$in": sticker_ids}
        }, {"_id": 0}).to_list(1000)
        
        other_inv_map = {item['sticker_id']: item['owned_qty'] for item in other_inventory}
        
        user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
        
        my_duplicates = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) >= 2]
        my_missing = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) == 0]
        other_duplicates = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) >= 2]
        other_missing = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) == 0]
        
        can_give = [sid for sid in my_duplicates if sid in other_missing]
        can_get = [sid for sid in other_duplicates if sid in my_missing]
        
        if can_give and can_get:
            matches.append({
                "type": "direct",
                "user": user,
                "give_stickers": [sticker_map[sid] for sid in can_give[:3]],
                "get_stickers": [sticker_map[sid] for sid in can_get[:3]],
                "net_gain": len(can_get)
            })
    
    matches.sort(key=lambda x: -x['net_gain'])
    return matches

@api_router.post("/offers")
async def create_offer(offer_input: OfferCreate, user_id: str = Depends(get_current_user)):
    membership = await db.album_members.find_one({"album_id": offer_input.album_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this album")
    
    offer = Offer(
        album_id=offer_input.album_id,
        from_user_id=user_id,
        to_user_id=offer_input.to_user_id,
        status='sent'
    )
    doc = offer.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.offers.insert_one(doc)
    
    for item in offer_input.give_items:
        offer_item = OfferItem(offer_id=offer.id, sticker_id=item['sticker_id'], direction='give', qty=item['qty'])
        await db.offer_items.insert_one(offer_item.model_dump())
    
    for item in offer_input.get_items:
        offer_item = OfferItem(offer_id=offer.id, sticker_id=item['sticker_id'], direction='get', qty=item['qty'])
        await db.offer_items.insert_one(offer_item.model_dump())
    
    return offer

@api_router.get("/offers")
async def get_offers(album_id: str, user_id: str = Depends(get_current_user)):
    sent_offers = await db.offers.find({
        "album_id": album_id,
        "from_user_id": user_id
    }, {"_id": 0}).to_list(100)
    
    received_offers = await db.offers.find({
        "album_id": album_id,
        "to_user_id": user_id
    }, {"_id": 0}).to_list(100)
    
    for offer in sent_offers + received_offers:
        items = await db.offer_items.find({"offer_id": offer['id']}, {"_id": 0}).to_list(100)
        offer['items'] = items
        
        from_user = await db.users.find_one({"id": offer['from_user_id']}, {"_id": 0})
        to_user = await db.users.find_one({"id": offer['to_user_id']}, {"_id": 0})
        offer['from_user'] = from_user
        offer['to_user'] = to_user
    
    return {"sent": sent_offers, "received": received_offers}

@api_router.patch("/offers/{offer_id}")
async def update_offer_status(offer_id: str, update: OfferUpdate, user_id: str = Depends(get_current_user)):
    offer = await db.offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    if offer['to_user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.offers.update_one(
        {"id": offer_id},
        {"$set": {"status": update.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Offer updated"}

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
