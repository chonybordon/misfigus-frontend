"""Database cleanup script for production.
Removes test users and their associated data.

Usage:
  python cleanup_db.py           # Dry run (shows what would be deleted)
  python cleanup_db.py --execute # Actually delete data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Patterns to identify test users
TEST_EMAIL_PATTERNS = [
    "@example.com",
    "test@",
    "testuser@",
    "demo@",
    "testbackend",
    "frontendtest",
    "lonelyuser",
    "uniquealone",
    "solo@",
    "newuser@",
    "prueba",
]

TEST_DISPLAY_NAME_PATTERNS = [
    "prueba",
    "test",
    "demo",
    "usuario de prueba",
    "nuevo usuario",
]

async def cleanup_database(dry_run: bool = True):
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("="*60)
    print("DATABASE CLEANUP SCRIPT")
    print("="*60)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("\n⚠️  EXECUTE MODE - Data will be deleted!\n")
    
    # Build query for test users
    email_conditions = [{"email": {"$regex": pattern, "$options": "i"}} for pattern in TEST_EMAIL_PATTERNS]
    display_name_conditions = [{"display_name": {"$regex": pattern, "$options": "i"}} for pattern in TEST_DISPLAY_NAME_PATTERNS]
    
    all_conditions = email_conditions + display_name_conditions
    
    # Find test users
    test_users = await db.users.find(
        {"$or": all_conditions},
        {"_id": 0, "id": 1, "email": 1, "display_name": 1}
    ).to_list(1000)
    
    if not test_users:
        print("✅ No test users found. Database is clean!")
        client.close()
        return
    
    print(f"Found {len(test_users)} test users to remove:")
    for user in test_users:
        display = user.get('display_name', 'N/A')
        print(f"  - {user['email']} (display: {display})")
    
    test_user_ids = [u['id'] for u in test_users]
    
    # Count related data
    memberships_count = await db.album_members.count_documents({"user_id": {"$in": test_user_ids}})
    activations_count = await db.user_album_activations.count_documents({"user_id": {"$in": test_user_ids}})
    inventory_count = await db.user_inventory.count_documents({"user_id": {"$in": test_user_ids}})
    offers_count = await db.offers.count_documents({
        "$or": [
            {"from_user_id": {"$in": test_user_ids}},
            {"to_user_id": {"$in": test_user_ids}}
        ]
    })
    invites_count = await db.invite_tokens.count_documents({"created_by_user_id": {"$in": test_user_ids}})
    
    print(f"\nRelated data to remove:")
    print(f"  - {memberships_count} album memberships")
    print(f"  - {activations_count} album activations")
    print(f"  - {inventory_count} inventory entries")
    print(f"  - {offers_count} offers")
    print(f"  - {invites_count} invite tokens")
    
    if dry_run:
        print("\n💡 Run with --execute to delete this data")
    else:
        print("\nDeleting data...")
        
        # Delete related data
        r1 = await db.album_members.delete_many({"user_id": {"$in": test_user_ids}})
        print(f"  ✓ Deleted {r1.deleted_count} album memberships")
        
        r2 = await db.user_album_activations.delete_many({"user_id": {"$in": test_user_ids}})
        print(f"  ✓ Deleted {r2.deleted_count} album activations")
        
        r3 = await db.user_inventory.delete_many({"user_id": {"$in": test_user_ids}})
        print(f"  ✓ Deleted {r3.deleted_count} inventory entries")
        
        r4 = await db.offers.delete_many({
            "$or": [
                {"from_user_id": {"$in": test_user_ids}},
                {"to_user_id": {"$in": test_user_ids}}
            ]
        })
        print(f"  ✓ Deleted {r4.deleted_count} offers")
        
        r5 = await db.invite_tokens.delete_many({"created_by_user_id": {"$in": test_user_ids}})
        print(f"  ✓ Deleted {r5.deleted_count} invite tokens")
        
        r6 = await db.users.delete_many({"id": {"$in": test_user_ids}})
        print(f"  ✓ Deleted {r6.deleted_count} users")
        
        print("\n✅ Database cleanup complete!")
    
    client.close()

if __name__ == "__main__":
    execute = "--execute" in sys.argv
    asyncio.run(cleanup_database(dry_run=not execute))
