#!/usr/bin/env python3
"""
User Data Cleanup Script for MisFigus
======================================
Removes ALL user data while preserving album templates and sticker definitions.

This script will DELETE:
- All users (real, demo, test)
- User album activations
- User inventories  
- Album memberships
- Exchanges
- Chats and chat messages
- Groups and group memberships
- Email invites
- User reputations

This script will KEEP:
- Album templates/definitions
- Sticker master data
- App configuration
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Collections to DELETE (user-generated data)
COLLECTIONS_TO_DELETE = [
    "users",
    "user_album_activations",
    "user_inventory", 
    "album_members",
    "exchanges",
    "chats",
    "chat_messages",
    "groups",
    "group_members",
    "email_invites",
    "user_reputation",
    "invite_tokens",  # Legacy invite tokens if they exist
]

# Collections to KEEP (template/master data)
COLLECTIONS_TO_KEEP = [
    "albums",
    "stickers",
]

async def cleanup_user_data():
    """Remove all user data while preserving album templates."""
    
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "sticker_swap")
    
    if not mongo_url:
        print("ERROR: MONGO_URL environment variable not set")
        return False
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 60)
    print("MisFigus User Data Cleanup")
    print("=" * 60)
    print(f"Database: {db_name}")
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # First, show what we're keeping
    print("Collections to KEEP (template data):")
    for coll_name in COLLECTIONS_TO_KEEP:
        try:
            count = await db[coll_name].count_documents({})
            print(f"  ✓ {coll_name}: {count} documents")
        except Exception as e:
            print(f"  - {coll_name}: (does not exist)")
    print()
    
    # Show what we're deleting
    print("Collections to DELETE (user data):")
    total_deleted = 0
    
    for coll_name in COLLECTIONS_TO_DELETE:
        try:
            count = await db[coll_name].count_documents({})
            if count > 0:
                print(f"  ✗ {coll_name}: {count} documents -> DELETING...")
                result = await db[coll_name].delete_many({})
                print(f"    Deleted {result.deleted_count} documents")
                total_deleted += result.deleted_count
            else:
                print(f"  - {coll_name}: 0 documents (empty)")
        except Exception as e:
            print(f"  - {coll_name}: (error: {str(e)})")
    
    print()
    print("=" * 60)
    print(f"CLEANUP COMPLETE")
    print(f"Total documents deleted: {total_deleted}")
    print(f"Finished at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Verify cleanup
    print()
    print("Verification - User collections should be empty:")
    for coll_name in COLLECTIONS_TO_DELETE:
        try:
            count = await db[coll_name].count_documents({})
            status = "✓ EMPTY" if count == 0 else f"✗ {count} remaining"
            print(f"  {coll_name}: {status}")
        except:
            print(f"  {coll_name}: (not found)")
    
    print()
    print("Verification - Template collections should be intact:")
    for coll_name in COLLECTIONS_TO_KEEP:
        try:
            count = await db[coll_name].count_documents({})
            print(f"  {coll_name}: {count} documents")
        except:
            print(f"  {coll_name}: (not found)")
    
    client.close()
    return True

if __name__ == "__main__":
    asyncio.run(cleanup_user_data())
