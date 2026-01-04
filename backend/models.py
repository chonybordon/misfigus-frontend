from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

# ============================================
# USER MODELS
# ============================================
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

# ============================================
# ALBUM MODELS (Album = template)
# ============================================
class Album(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    year: int
    category: str
    status: str = 'active'
    has_placeholder: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============================================
# GROUP MODELS (Group = private instance of an album)
# ============================================
class Group(BaseModel):
    """A private group for a specific album. Users can only see members/matches within their group."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    album_id: str  # Which album template this group is for
    name: str  # Group name (e.g., "Familia Bordon")
    owner_id: str  # User who created the group
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupMember(BaseModel):
    """Membership in a group. Users can be members of multiple groups."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    user_id: str
    invited_by_user_id: Optional[str] = None
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupCreate(BaseModel):
    album_id: str
    name: str

# ============================================
# EMAIL INVITE MODELS
# ============================================
class EmailInvite(BaseModel):
    """Email-based invite with a 6-digit code. Single-use, expires in 1 hour."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    invited_email: str  # Email address being invited
    invite_code: str  # 6-digit code
    created_by_user_id: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmailInviteCreate(BaseModel):
    email: str

class EmailInviteAccept(BaseModel):
    invite_code: str

# ============================================
# LEGACY INVITE TOKEN (deprecated, kept for compatibility)
# ============================================
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

# ============================================
# LEGACY ALBUM MEMBER (deprecated, use GroupMember)
# ============================================
class AlbumMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    album_id: str
    user_id: str
    invited_by_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============================================
# STICKER MODELS
# ============================================
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
    """User's sticker inventory - scoped by group_id for privacy."""
    model_config = ConfigDict(extra="ignore")
    user_id: str
    group_id: str  # Added: inventory is per-group
    sticker_id: str
    owned_qty: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryUpdate(BaseModel):
    sticker_id: str
    owned_qty: int

# ============================================
# OFFER MODELS
# ============================================
class Offer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str  # Added: offers are scoped by group
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
    group_id: str
    to_user_id: str
    give_items: list
    get_items: list

class OfferUpdate(BaseModel):
    status: str

# ============================================
# CHAT MODELS (Phase 2, but defining now)
# ============================================
class Chat(BaseModel):
    """1-to-1 chat between two users within the same group."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    user_a_id: str  # One user
    user_b_id: str  # Other user
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    sender_id: str  # 'system' for system messages
    content: str
    is_system: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
