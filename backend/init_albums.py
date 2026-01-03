import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import json
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def init_albums():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Clear existing albums and stickers
    await db.albums.delete_many({})
    await db.stickers.delete_many({})
    
    albums_data = [
        # AVAILABLE albums - can be activated by users
        {
            "id": str(uuid.uuid4()),
            "name": "FIFA World Cup Qatar 2022",
            "year": 2022,
            "category": "Fútbol",
            "status": "active",
            "has_placeholder": False
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Pokémon",
            "year": 2024,
            "category": "Trading Cards",
            "status": "active",
            "has_placeholder": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Dragon Ball",
            "year": 2024,
            "category": "Anime",
            "status": "active",
            "has_placeholder": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Marvel",
            "year": 2024,
            "category": "Superhéroes",
            "status": "active",
            "has_placeholder": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Disney",
            "year": 2024,
            "category": "Entretenimiento",
            "status": "active",
            "has_placeholder": True
        },
        # COMING SOON albums - not activable yet
        {
            "id": str(uuid.uuid4()),
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
    qatar_album_id = albums_data[0]['id']
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
    placeholder_albums = albums_data[1:5]  # Skip Qatar 2022, get next 4
    
    for album in placeholder_albums:
        placeholder_stickers = []
        for i in range(1, 201):  # Create 200 placeholder stickers
            sticker = {
                "id": str(uuid.uuid4()),
                "album_id": album['id'],
                "number": i,
                "name": f"Figurita #{i}",
                "team": "Colección",
                "category": "General"
            }
            placeholder_stickers.append(sticker)
            await db.stickers.insert_one(sticker)
        
        print(f"Created 200 placeholder stickers for {album['name']}")
    
    client.close()
    print("\n✅ Album initialization complete!")
    print("Note: Pokémon, Dragon Ball, Marvel, Disney use placeholder stickers (1-200)")

if __name__ == "__main__":
    asyncio.run(init_albums())
