import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Album i18n key mappings
ALBUM_I18N_KEYS = {
    "bc32fecb-f640-4d00-880d-5043bc112d4b": {
        "name_key": "mundial_2022",
        "category_key": "sports"
    },
    "ecc59406-6ec2-4c32-b721-8d50bd04a89e": {
        "name_key": "criaturas_fantasticas",
        "category_key": "trading_cards"
    },
    "9da0b5c7-0c70-454d-89c5-257587b9e1a8": {
        "name_key": "guerreros_anime",
        "category_key": "anime"
    },
    "e7afe077-cab9-4fa5-95bc-dfc5f56c51d6": {
        "name_key": "heroes_multiverso",
        "category_key": "superheroes"
    },
    "40ea7629-4aea-4842-b84d-972d9abf6ff7": {
        "name_key": "personajes_animados",
        "category_key": "entertainment"
    },
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
        "name_key": "mundial_2026",
        "category_key": "sports"
    }
}

async def add_i18n_keys_to_albums():
    """Add i18n keys (name_key, category_key) to all albums for proper localization."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 60)
    print("ADDING i18n KEYS TO ALBUMS")
    print("=" * 60)
    
    for album_id, keys in ALBUM_I18N_KEYS.items():
        result = await db.albums.update_one(
            {"id": album_id},
            {"$set": keys}
        )
        if result.modified_count > 0:
            print(f"  ✅ Added keys to album {album_id}: name_key={keys['name_key']}, category_key={keys['category_key']}")
        else:
            # Check if album exists and already has keys
            album = await db.albums.find_one({"id": album_id})
            if album:
                if album.get('name_key') == keys['name_key']:
                    print(f"  ℹ️  Album {album_id} already has correct keys")
                else:
                    print(f"  ⚠️  Album {album_id} exists but update failed")
            else:
                print(f"  ⚠️  Album not found: {album_id}")
    
    # Verify all albums now have i18n keys
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    async for album in db.albums.find({}, {"_id": 0, "id": 1, "name": 1, "name_key": 1, "category_key": 1}):
        has_name_key = "✅" if album.get("name_key") else "❌"
        has_category_key = "✅" if album.get("category_key") else "❌"
        print(f"  {album.get('name', 'Unknown')}: name_key={has_name_key}, category_key={has_category_key}")
    
    client.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    asyncio.run(add_i18n_keys_to_albums())
