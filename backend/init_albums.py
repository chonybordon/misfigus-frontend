import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import json
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Fixed album IDs for consistency
ALBUM_IDS = {
    "qatar_2022": "bc32fecb-f640-4d00-880d-5043bc112d4b",
    "pokemon": "ecc59406-6ec2-4c32-b721-8d50bd04a89e",
    "dragon_ball": "9da0b5c7-0c70-454d-89c5-257587b9e1a8",
    "marvel": "e7afe077-cab9-4fa5-95bc-dfc5f56c51d6",
    "disney": "40ea7629-4aea-4842-b84d-972d9abf6ff7",
    "world_cup_2026": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}

async def init_albums():
    """Initialize albums catalog. Only runs when SEED_DEV_DATA=true or albums are empty."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Check if we should seed
    seed_dev_data = os.environ.get('SEED_DEV_DATA', 'false').lower() == 'true'
    existing_albums = await db.albums.count_documents({})
    
    if existing_albums > 0 and not seed_dev_data:
        print("Albums already exist. Skipping initialization.")
        print("Set SEED_DEV_DATA=true to force re-initialization.")
        client.close()
        return
    
    if seed_dev_data:
        print("SEED_DEV_DATA=true - Re-initializing albums...")
        # Clear existing albums and stickers only
        await db.albums.delete_many({})
        await db.stickers.delete_many({})
    
    albums_data = [
        # AVAILABLE albums - can be activated by users
        {
            "id": ALBUM_IDS["qatar_2022"],
            "name": "FIFA World Cup Qatar 2022",
            "year": 2022,
            "category": "Fútbol",
            "status": "active",
            "has_placeholder": False
        },
        {
            "id": ALBUM_IDS["pokemon"],
            "name": "Pokémon",
            "year": 2024,
            "category": "Trading Cards",
            "status": "active",
            "has_placeholder": True
        },
        {
            "id": ALBUM_IDS["dragon_ball"],
            "name": "Dragon Ball",
            "year": 2024,
            "category": "Anime",
            "status": "active",
            "has_placeholder": True
        },
        {
            "id": ALBUM_IDS["marvel"],
            "name": "Marvel",
            "year": 2024,
            "category": "Superhéroes",
            "status": "active",
            "has_placeholder": True
        },
        {
            "id": ALBUM_IDS["disney"],
            "name": "Disney",
            "year": 2024,
            "category": "Entretenimiento",
            "status": "active",
            "has_placeholder": True
        },
        # COMING SOON albums - not activable yet
        {
            "id": ALBUM_IDS["world_cup_2026"],
            "name": "FIFA World Cup 2026",
            "year": 2026,
            "category": "Fútbol",
            "status": "coming_soon",
            "has_placeholder": False
        }
    ]
    
    for album_data in albums_data:
        await db.albums.insert_one(album_data)
        print(f"Created album: {album_data['name']} ({album_data['status']})")
    
    # Load Qatar 2022 stickers (real dataset)
    qatar_album_id = ALBUM_IDS["qatar_2022"]
    stickers_path = ROOT_DIR / 'qatar_stickers.json'
    
    with open(stickers_path, 'r', encoding='utf-8') as f:
        stickers_data = json.load(f)
    
    for sticker_data in stickers_data:
        sticker = {
            "id": str(uuid.uuid4()),
            "album_id": qatar_album_id,
            **sticker_data
        }
        await db.stickers.insert_one(sticker)
    
    print(f"Loaded {len(stickers_data)} stickers for Qatar 2022 album")
    
    # Create placeholder stickers for other ACTIVE albums (Pokémon, Dragon Ball, Marvel, Disney)
    placeholder_album_keys = ["pokemon", "dragon_ball", "marvel", "disney"]
    
    for key in placeholder_album_keys:
        album_id = ALBUM_IDS[key]
        album_name = [a['name'] for a in albums_data if a['id'] == album_id][0]
        
        for i in range(1, 201):  # Create 200 placeholder stickers
            sticker = {
                "id": str(uuid.uuid4()),
                "album_id": album_id,
                "number": i,
                "name": f"Figurita #{i}",
                "team": "Colección",
                "category": "General"
            }
            await db.stickers.insert_one(sticker)
        
        print(f"Created 200 placeholder stickers for {album_name}")
    
    client.close()
    print("\n✅ Album initialization complete!")
    print("Note: No test users are created. Real users will register via OTP.")

if __name__ == "__main__":
    asyncio.run(init_albums())
