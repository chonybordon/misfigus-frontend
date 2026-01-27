import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Album name mappings (ID -> new name)
ALBUM_NAME_UPDATES = {
    "bc32fecb-f640-4d00-880d-5043bc112d4b": {
        "name": "Álbum Mundial de Fútbol 2022",
        "category": "Fútbol"
    },
    "ecc59406-6ec2-4c32-b721-8d50bd04a89e": {
        "name": "Criaturas Fantásticas",
        "category": "Cartas coleccionables"
    },
    "9da0b5c7-0c70-454d-89c5-257587b9e1a8": {
        "name": "Guerreros del Anime",
        "category": "Anime"
    },
    "e7afe077-cab9-4fa5-95bc-dfc5f56c51d6": {
        "name": "Héroes del Multiverso",
        "category": "Superhéroes"
    },
    "40ea7629-4aea-4842-b84d-972d9abf6ff7": {
        "name": "Personajes Animados",
        "category": "Entretenimiento"
    },
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
        "name": "Álbum Mundial de Fútbol 2026",
        "category": "Fútbol"
    }
}

async def update_albums_and_stickers():
    """Update album names and sticker labels to remove trademarked content."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 60)
    print("TRADEMARK CLEANUP MIGRATION")
    print("=" * 60)
    
    # PART 1: Update album names
    print("\n📋 Updating album names...")
    for album_id, updates in ALBUM_NAME_UPDATES.items():
        result = await db.albums.update_one(
            {"id": album_id},
            {"$set": updates}
        )
        if result.modified_count > 0:
            print(f"  ✅ Updated album: {updates['name']}")
        else:
            # Check if album exists
            album = await db.albums.find_one({"id": album_id})
            if album:
                print(f"  ℹ️  Album already has name: {album.get('name')}")
            else:
                print(f"  ⚠️  Album not found: {album_id}")
    
    # PART 2: Update stickers for football album
    qatar_album_id = "bc32fecb-f640-4d00-880d-5043bc112d4b"
    
    print("\n⚽ Updating football album stickers...")
    
    # Load the updated sticker data
    stickers_path = ROOT_DIR / 'qatar_stickers.json'
    with open(stickers_path, 'r', encoding='utf-8') as f:
        new_stickers_data = json.load(f)
    
    # Create a lookup by number
    sticker_updates = {s['number']: s for s in new_stickers_data}
    
    # Update each sticker
    updated_count = 0
    for number, sticker_data in sticker_updates.items():
        result = await db.stickers.update_one(
            {"album_id": qatar_album_id, "number": number},
            {"$set": {
                "name": sticker_data["name"],
                "team": sticker_data["team"],
                "category": sticker_data["category"]
            }}
        )
        if result.modified_count > 0:
            updated_count += 1
    
    print(f"  ✅ Updated {updated_count} stickers in football album")
    
    # Summary of changes
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print("\n📖 Album Name Changes:")
    print("  • FIFA World Cup Qatar 2022 → Álbum Mundial de Fútbol 2022")
    print("  • FIFA World Cup 2026 → Álbum Mundial de Fútbol 2026")
    print("  • Pokémon → Criaturas Fantásticas")
    print("  • Dragon Ball → Guerreros del Anime")
    print("  • Marvel → Héroes del Multiverso")
    print("  • Disney → Personajes Animados")
    print("\n🏷️  Sticker Label Changes (examples):")
    print("  • FWC 2022 Logo → Emblema del Torneo")
    print("  • World Cup Trophy → Trofeo del Campeonato")
    print("  • Qatar 2022 → Evento 2022")
    print("  • [Country] Badge → Emblema de [País]")
    print("  • FIFA (team) → Torneo")
    print("\n✅ Migration complete!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_albums_and_stickers())
