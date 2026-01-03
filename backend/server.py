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

from models import (
    User, UserCreate, OTPVerify, Group, GroupCreate, GroupMember,
    InviteToken, InviteCreate, Album, Sticker, UserInventory, InventoryUpdate,
    Offer, OfferCreate, OfferUpdate, OfferItem, ChatThread, Message, MessageCreate,
    Block, Report, Notification
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

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    return {"message": "OTP sent", "email": user_input.email}

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

@api_router.post("/groups", response_model=Group)
async def create_group(group_input: GroupCreate, user_id: str = Depends(get_current_user)):
    group = Group(name=group_input.name)
    doc = group.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.groups.insert_one(doc)
    
    member = GroupMember(group_id=group.id, user_id=user_id, role='member')
    member_doc = member.model_dump()
    member_doc['created_at'] = member_doc['created_at'].isoformat()
    await db.group_members.insert_one(member_doc)
    
    album = Album(group_id=group.id, name="FIFA World Cup Qatar 2022", year=2022)
    album_doc = album.model_dump()
    album_doc['created_at'] = album_doc['created_at'].isoformat()
    await db.albums.insert_one(album_doc)
    
    stickers_path = ROOT_DIR / 'qatar_stickers.json'
    with open(stickers_path, 'r', encoding='utf-8') as f:
        stickers_data = json.load(f)
    
    for sticker_data in stickers_data:
        sticker = Sticker(album_id=album.id, **sticker_data)
        sticker_doc = sticker.model_dump()
        await db.stickers.insert_one(sticker_doc)
    
    return group

@api_router.get("/groups")
async def get_groups(user_id: str = Depends(get_current_user)):
    memberships = await db.group_members.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    group_ids = [m['group_id'] for m in memberships]
    
    groups = await db.groups.find({"id": {"$in": group_ids}}, {"_id": 0}).to_list(100)
    return groups

@api_router.get("/groups/{group_id}")
async def get_group(group_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.group_members.find_one({"group_id": group_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    group = await db.groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members = await db.group_members.find({"group_id": group_id}, {"_id": 0}).to_list(100)
    member_ids = [m['user_id'] for m in members]
    users = await db.users.find({"id": {"$in": member_ids}}, {"_id": 0}).to_list(100)
    
    group['members'] = users
    group['member_count'] = len(users)
    
    return group

@api_router.post("/groups/{group_id}/invites")
async def create_invite(group_id: str, invite_input: InviteCreate, user_id: str = Depends(get_current_user)):
    membership = await db.group_members.find_one({"group_id": group_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    invite_count = await db.invite_tokens.count_documents({
        "group_id": group_id,
        "created_by_user_id": user_id
    })
    
    group = await db.groups.find_one({"id": group_id}, {"_id": 0})
    if invite_count >= group['invite_limit_per_user']:
        raise HTTPException(status_code=400, detail="Invite limit reached")
    
    invite = InviteToken(
        group_id=group_id,
        invited_email=invite_input.invited_email,
        created_by_user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    doc = invite.model_dump()
    doc['expires_at'] = doc['expires_at'].isoformat()
    await db.invite_tokens.insert_one(doc)
    
    return {"token": invite.token, "expires_at": invite.expires_at}

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
    
    existing = await db.group_members.find_one({"group_id": invite['group_id'], "user_id": user_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")
    
    member = GroupMember(
        group_id=invite['group_id'],
        user_id=user_id,
        role='member',
        invited_by_user_id=invite['created_by_user_id']
    )
    member_doc = member.model_dump()
    member_doc['created_at'] = member_doc['created_at'].isoformat()
    await db.group_members.insert_one(member_doc)
    
    await db.invite_tokens.update_one(
        {"token": token},
        {"$set": {"used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Joined group successfully"}

@api_router.get("/albums")
async def get_albums(group_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.group_members.find_one({"group_id": group_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    albums = await db.albums.find({"group_id": group_id}, {"_id": 0}).to_list(100)
    return albums

@api_router.get("/albums/{album_id}/stickers")
async def get_stickers(album_id: str, user_id: str = Depends(get_current_user)):
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    return stickers

@api_router.get("/inventory")
async def get_inventory(album_id: str, user_id: str = Depends(get_current_user)):
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    
    inventory_items = await db.user_inventory.find({
        "user_id": user_id,
        "sticker_id": {"$in": [s['id'] for s in stickers]}
    }, {"_id": 0}).to_list(1000)
    
    inventory_map = {item['sticker_id']: item['owned_qty'] for item in inventory_items}
    
    for sticker in stickers:
        sticker['owned_qty'] = inventory_map.get(sticker['id'], 0)
    
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
async def get_matches(group_id: str, album_id: str, user_id: str = Depends(get_current_user)):
    membership = await db.group_members.find_one({"group_id": group_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    stickers = await db.stickers.find({"album_id": album_id}, {"_id": 0}).to_list(1000)
    sticker_ids = [s['id'] for s in stickers]
    
    my_inventory = await db.user_inventory.find({
        "user_id": user_id,
        "sticker_id": {"$in": sticker_ids}
    }, {"_id": 0}).to_list(1000)
    
    my_inv_map = {item['sticker_id']: item['owned_qty'] for item in my_inventory}
    
    members = await db.group_members.find({"group_id": group_id}, {"_id": 0}).to_list(100)
    other_user_ids = [m['user_id'] for m in members if m['user_id'] != user_id]
    
    matches = []
    
    for other_user_id in other_user_ids:
        other_inventory = await db.user_inventory.find({
            "user_id": other_user_id,
            "sticker_id": {"$in": sticker_ids}
        }, {"_id": 0}).to_list(1000)
        
        other_inv_map = {item['sticker_id']: item['owned_qty'] for item in other_inventory}
        
        user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
        
        my_duplicates = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) > 1]
        my_missing = [sid for sid in sticker_ids if my_inv_map.get(sid, 0) == 0]
        other_duplicates = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) > 1]
        other_missing = [sid for sid in sticker_ids if other_inv_map.get(sid, 0) == 0]
        
        can_give = [sid for sid in my_duplicates if sid in other_missing]
        can_get = [sid for sid in other_duplicates if sid in my_missing]
        
        if can_give and can_get:
            sticker_map = {s['id']: s for s in stickers}
            matches.append({
                "type": "direct",
                "user": user,
                "give_stickers": [sticker_map[sid] for sid in can_give[:3]],
                "get_stickers": [sticker_map[sid] for sid in can_get[:3]],
                "net_gain": len(can_get) - len(can_give)
            })
        elif can_give:
            sticker_map = {s['id']: s for s in stickers}
            matches.append({
                "type": "partial",
                "user": user,
                "give_stickers": [sticker_map[sid] for sid in can_give[:3]],
                "get_stickers": [],
                "net_gain": -len(can_give)
            })
    
    matches.sort(key=lambda x: -x['net_gain'])
    return matches

@api_router.post("/offers")
async def create_offer(offer_input: OfferCreate, user_id: str = Depends(get_current_user)):
    membership = await db.group_members.find_one({"group_id": offer_input.group_id, "user_id": user_id}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    offer = Offer(
        group_id=offer_input.group_id,
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
    
    notification = Notification(
        user_id=offer_input.to_user_id,
        type='new_offer',
        content=f"New offer from {user_id}"
    )
    notif_doc = notification.model_dump()
    notif_doc['created_at'] = notif_doc['created_at'].isoformat()
    await db.notifications.insert_one(notif_doc)
    
    return offer

@api_router.get("/offers")
async def get_offers(group_id: str, user_id: str = Depends(get_current_user)):
    sent_offers = await db.offers.find({
        "group_id": group_id,
        "from_user_id": user_id
    }, {"_id": 0}).to_list(100)
    
    received_offers = await db.offers.find({
        "group_id": group_id,
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
    
    if update.status == 'accepted':
        notification = Notification(
            user_id=offer['from_user_id'],
            type='offer_accepted',
            content=f"Your offer was accepted"
        )
        notif_doc = notification.model_dump()
        notif_doc['created_at'] = notif_doc['created_at'].isoformat()
        await db.notifications.insert_one(notif_doc)
    
    return {"message": "Offer updated"}

@api_router.post("/offers/{offer_id}/apply")
async def apply_offer(offer_id: str, user_id: str = Depends(get_current_user)):
    offer = await db.offers.find_one({"id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    if offer['to_user_id'] != user_id and offer['from_user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if offer['status'] != 'accepted':
        raise HTTPException(status_code=400, detail="Offer must be accepted first")
    
    items = await db.offer_items.find({"offer_id": offer_id}, {"_id": 0}).to_list(100)
    
    for item in items:
        if item['direction'] == 'give':
            from_user = offer['from_user_id']
            to_user = offer['to_user_id']
            
            from_inv = await db.user_inventory.find_one({"user_id": from_user, "sticker_id": item['sticker_id']}, {"_id": 0})
            if from_inv:
                new_qty = max(0, from_inv['owned_qty'] - item['qty'])
                await db.user_inventory.update_one(
                    {"user_id": from_user, "sticker_id": item['sticker_id']},
                    {"$set": {"owned_qty": new_qty}}
                )
            
            to_inv = await db.user_inventory.find_one({"user_id": to_user, "sticker_id": item['sticker_id']}, {"_id": 0})
            if to_inv:
                await db.user_inventory.update_one(
                    {"user_id": to_user, "sticker_id": item['sticker_id']},
                    {"$set": {"owned_qty": to_inv['owned_qty'] + item['qty']}}
                )
            else:
                new_inv = UserInventory(user_id=to_user, sticker_id=item['sticker_id'], owned_qty=item['qty'])
                doc = new_inv.model_dump()
                doc['updated_at'] = doc['updated_at'].isoformat()
                await db.user_inventory.insert_one(doc)
    
    return {"message": "Inventories updated"}

@api_router.get("/chat/threads")
async def get_threads(group_id: str, user_id: str = Depends(get_current_user)):
    threads = await db.chat_threads.find({
        "group_id": group_id,
        "$or": [{"user_a_id": user_id}, {"user_b_id": user_id}]
    }, {"_id": 0}).to_list(100)
    
    for thread in threads:
        other_user_id = thread['user_b_id'] if thread['user_a_id'] == user_id else thread['user_a_id']
        other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
        thread['other_user'] = other_user
        
        last_message = await db.messages.find_one(
            {"thread_id": thread['id']},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        thread['last_message'] = last_message
    
    return threads

@api_router.get("/chat/threads/{other_user_id}")
async def get_or_create_thread(group_id: str, other_user_id: str, user_id: str = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({
        "group_id": group_id,
        "$or": [
            {"user_a_id": user_id, "user_b_id": other_user_id},
            {"user_a_id": other_user_id, "user_b_id": user_id}
        ]
    }, {"_id": 0})
    
    if not thread:
        new_thread = ChatThread(group_id=group_id, user_a_id=user_id, user_b_id=other_user_id)
        doc = new_thread.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.chat_threads.insert_one(doc)
        thread = doc
    
    messages = await db.messages.find({"thread_id": thread['id']}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    
    return {"thread": thread, "messages": messages}

@api_router.post("/chat/messages")
async def send_message(group_id: str, thread_id: str, message_input: MessageCreate, user_id: str = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if user_id not in [thread['user_a_id'], thread['user_b_id']]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    message = Message(
        thread_id=thread_id,
        from_user_id=user_id,
        to_user_id=message_input.to_user_id,
        text=message_input.text
    )
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.messages.insert_one(doc)
    
    notification = Notification(
        user_id=message_input.to_user_id,
        type='new_message',
        content=f"New message from {user_id}"
    )
    notif_doc = notification.model_dump()
    notif_doc['created_at'] = notif_doc['created_at'].isoformat()
    await db.notifications.insert_one(notif_doc)
    
    return message

@api_router.get("/notifications")
async def get_notifications(user_id: str = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    return notifications

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user_id: str = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": user_id},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

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
