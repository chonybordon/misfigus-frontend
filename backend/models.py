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
    # Location & Radius
    location_zone: Optional[str] = None  # Approximate zone (e.g., "Caballito, CABA")
    location_lat: Optional[float] = None  # Approximate latitude
    location_lng: Optional[float] = None  # Approximate longitude
    location_updated_at: Optional[datetime] = None
    search_radius_km: int = 5  # Default 5km, allowed: 3, 5, 10
    search_radius_updated_at: Optional[datetime] = None
    # Terms acceptance
    terms_accepted: bool = False
    terms_version: Optional[str] = None
    terms_accepted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    language: Optional[str] = None

class UserLocationUpdate(BaseModel):
    zone: str  # Approximate zone name
    lat: float  # Approximate latitude
    lng: float  # Approximate longitude

class UserRadiusUpdate(BaseModel):
    radius_km: int  # 3, 5, or 10

class TermsAcceptance(BaseModel):
    version: str  # Terms version being accepted

class OTPVerify(BaseModel):
    email: str
    otp: str

# Allowed search radius values
ALLOWED_RADIUS_VALUES = [3, 5, 10]
# Cooldown for location/radius changes (7 days)
SETTINGS_CHANGE_COOLDOWN_DAYS = 7
# Current terms version
CURRENT_TERMS_VERSION = "1.0"

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

# ============================================
# EXCHANGE MODELS (Local Exchange Lifecycle)
# ============================================
class Exchange(BaseModel):
    """
    A real exchange between two users with mutual sticker matches.
    Exchange = the only context where chat is allowed.
    """
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    album_id: str
    user_a_id: str
    user_b_id: str
    # Stickers offered by each user (list of sticker IDs)
    user_a_offers: List[str] = []  # Stickers A gives to B
    user_b_offers: List[str] = []  # Stickers B gives to A
    # Status: pending, completed, failed, expired
    status: str = 'pending'
    # Confirmation tracking
    user_a_confirmed: Optional[bool] = None  # True=👍, False=👎, None=not yet
    user_b_confirmed: Optional[bool] = None
    user_a_confirmed_at: Optional[datetime] = None
    user_b_confirmed_at: Optional[datetime] = None
    # Failure reason (if 👎)
    user_a_failure_reason: Optional[str] = None
    user_b_failure_reason: Optional[str] = None
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # 7 days from creation

class ExchangeCreate(BaseModel):
    album_id: str
    partner_user_id: str

class ExchangeConfirm(BaseModel):
    confirmed: bool  # True=👍, False=👎
    failure_reason: Optional[str] = None  # Required if confirmed=False

# Failure reasons for 👎
EXCHANGE_FAILURE_REASONS = [
    'no_show',           # Did not show up
    'cancelled',         # Cancelled without notice
    'attempted_sale',    # Attempted to sell
    'inappropriate'      # Inappropriate behavior
]

# ============================================
# REPUTATION MODELS (Automatic, Non-Social)
# ============================================
class UserReputation(BaseModel):
    """
    User reputation computed from exchange history.
    Status: trusted, under_review, restricted
    """
    model_config = ConfigDict(extra="ignore")
    user_id: str
    # Counters
    total_exchanges: int = 0
    successful_exchanges: int = 0
    failed_exchanges: int = 0
    consecutive_failures: int = 0
    # Status
    status: str = 'trusted'  # trusted, under_review, restricted
    # Restrictions
    invisible_until: Optional[datetime] = None  # 48h invisibility
    suspended_at: Optional[datetime] = None
    # Last update
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Reputation thresholds
REPUTATION_CONSECUTIVE_FAIL_THRESHOLD = 2   # 2 consecutive → 48h invisible
REPUTATION_TOTAL_FAIL_THRESHOLD = 5          # 5 total → suspended

