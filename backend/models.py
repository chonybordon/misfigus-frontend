from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: str
    display_name: Optional[str] = None
    verified: bool = False
    language: str = 'es'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    language: Optional[str] = None

class OTPVerify(BaseModel):
    email: str
    otp: str

class Album(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    year: int
    category: str
    status: str = 'active'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlbumMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    album_id: str
    user_id: str
    invited_by_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InviteToken(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    album_id: str
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_by_user_id: str

class InviteCreate(BaseModel):
    album_id: str

class Sticker(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    album_id: str
    number: int
    name: str
    team: str
    category: str
    image_url: Optional[str] = None

class UserInventory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    sticker_id: str
    owned_qty: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryUpdate(BaseModel):
    sticker_id: str
    owned_qty: int

class Offer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    album_id: str
    from_user_id: str
    to_user_id: str
    status: str = 'sent'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OfferItem(BaseModel):
    offer_id: str
    sticker_id: str
    direction: str
    qty: int

class OfferCreate(BaseModel):
    album_id: str
    to_user_id: str
    give_items: list
    get_items: list

class OfferUpdate(BaseModel):
    status: str
