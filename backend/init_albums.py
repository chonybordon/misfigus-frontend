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
        # ACTIVE albums - can be activated by users
        {
            "id": str(uuid.uuid4()),
            "name": "FIFA World Cup Qatar 2022",
            "year": 2022,
            "category": "Fútbol",
            "status": "active"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Pokémon",
            "year": 2024,
            "category": "Trading Cards",
            "status": "active"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Dragon Ball",
            "year": 2024,
            "category": "Anime",
            "status": "active"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Marvel",
            "year": 2024,
            "category": "Superhéroes",
            "status": "active"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Disney",
            "year": 2024,
            "category": "Entretenimiento",
            "status": "active"
        },
        # COMING SOON albums - not activable yet
        {
            "id": str(uuid.uuid4()),
            "name": "FIFA World Cup 2026",
            "year": 2026,
            "category": "Fútbol",
            "status": "coming_soon"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Copa América 2024",
            "year": 2024,
            "category": "Fútbol",
            "status": "coming_soon"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "UEFA Champions League",
            "year": 2024,
            "category": "Fútbol",
            "status": "coming_soon"
        }
    ]
    
    for album_data in albums_data:
        await db.albums.insert_one(album_data)
        print(f"Created album: {album_data['name']} ({album_data['status']})")
    
    # Load Qatar 2022 stickers for the first active album
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
    print(f"\nNote: Other ACTIVE albums (Pokémon, Dragon Ball, Marvel, Disney)")
    print(f"are activable but show 'Figuritas próximamente' until datasets are loaded.")
    
    client.close()
    print("\nAlbum initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_albums())
