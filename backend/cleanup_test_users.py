"""
Script to remove test users from production database.
Run this manually when needed: python cleanup_test_users.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "sticker_swap_db")

# Patterns to identify test users
TEST_PATTERNS = [
    "@example.com",
    "test@",
    "testuser@",
    "demo@",
    "testbackend",
    "frontendtest",
    "lonelyuser",
    "uniquealone",
    "solo@",
    "newuser@example.com",
]

async def cleanup_test_users():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find test users
    test_conditions = [{"email": {"$regex": pattern, "$options": "i"}} for pattern in TEST_PATTERNS]
    test_users = await db.users.find({"$or": test_conditions}, {"_id": 0, "id": 1, "email": 1}).to_list(1000)
    
    if not test_users:
        print("No test users found.")
        return
    
    print(f"Found {len(test_users)} test users:")
    for user in test_users:
        print(f"  - {user['email']} (ID: {user['id']})")
    
    # Get confirmation
    confirm = input("\nDelete these users and their data? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    test_user_ids = [u['id'] for u in test_users]
    
    # Remove user-related data
    print("\nCleaning up...")
    
    # Remove album memberships
    result = await db.album_members.delete_many({"user_id": {"$in": test_user_ids}})
    print(f"  - Removed {result.deleted_count} album memberships")
    
    # Remove album activations
    result = await db.user_album_activations.delete_many({"user_id": {"$in": test_user_ids}})
    print(f"  - Removed {result.deleted_count} album activations")
    
    # Remove inventories
    result = await db.user_inventory.delete_many({"user_id": {"$in": test_user_ids}})
    print(f"  - Removed {result.deleted_count} inventory entries")
    
    # Remove offers
    result = await db.offers.delete_many({"$or": [
        {"from_user_id": {"$in": test_user_ids}},
        {"to_user_id": {"$in": test_user_ids}}
    ]})
    print(f"  - Removed {result.deleted_count} offers")
    
    # Remove users
    result = await db.users.delete_many({"id": {"$in": test_user_ids}})
    print(f"  - Removed {result.deleted_count} users")
    
    print("\nCleanup complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_test_users())
