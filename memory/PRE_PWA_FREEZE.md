# MisFigus App - Pre-PWA Freeze Checkpoint
## Date: January 2025

---

## 1. CURRENT WORKING FEATURES CHECKLIST

### ✅ Authentication
- [x] OTP login via email (Resend integration)
- [x] OTP verification with 10-minute expiry
- [x] JWT token-based auth
- [x] DEV_MODE with console OTP fallback
- [x] Email normalization (trim + lowercase)

### ✅ User Onboarding
- [x] Language selection (ES, EN, PT, FR, DE, IT)
- [x] Name setup
- [x] Location selection (country + city)
- [x] Terms & conditions acceptance
- [x] Onboarding completion tracking

### ✅ Album Management
- [x] Album list with categories
- [x] Album activation/deactivation
- [x] Plan-based album limits (Free: 1, Plus: 2, Unlimited: ∞)
- [x] Album detail view with stats
- [x] Legal disclaimer for fan-made content
- [x] i18n support for album names/categories

### ✅ Inventory System
- [x] "Mi inventario" tab - editable (set owned quantity)
- [x] "Faltan" tab - read-only (shows missing stickers)
- [x] "Duplicados" tab - read-only (shows duplicates)
- [x] Sticker grid with sections
- [x] Quantity controls (0, 1, 2+)
- [x] Progress tracking (total, owned, missing, duplicates)

### ✅ Exchange/Match System
- [x] Match algorithm (mutual needs/offers)
- [x] Exchange creation with partner
- [x] Three-tab navigation: New / Active / Completed
- [x] Badge counts on all tabs
- [x] Direct navigation to exchange detail
- [x] Exchange status tracking (pending, completed, failed)

### ✅ Chat System
- [x] Real-time chat polling (2s interval)
- [x] System messages (exchange started, etc.)
- [x] Read-only mode for completed exchanges
- [x] Auto-scroll on new messages
- [x] Chat limit enforcement on first message

### ✅ Subscription Plans
- [x] Three-tier system: Free / Plus / Unlimited
- [x] Plan limits enforced:
  - Free: 1 album, 1 chat/day
  - Plus: 2 albums, 5 chats/day
  - Unlimited: no limits
- [x] Chat counting on both creation AND reply
- [x] Daily reset of chat counters
- [x] Upgrade modal (Plus/Unlimited options)
- [x] Downgrade with album limit check
- [x] Usage stats display (counters)
- [x] **MOCKED payments** (no Stripe)

### ✅ User Reputation
- [x] Reputation badges (new, trusted, under_review, restricted)
- [x] Exchange outcome tracking
- [x] Failure threshold enforcement

### ✅ Settings
- [x] Profile display name edit
- [x] Location change (with cooldown)
- [x] Search radius adjustment
- [x] Language switching
- [x] Subscription management
- [x] Account deletion

### ✅ Error Handling
- [x] Safe error message rendering (no raw objects)
- [x] Upgrade modal on limit exceeded
- [x] Generic error fallbacks
- [x] Backend error code translation

### ✅ Internationalization (i18n)
- [x] 6 languages: ES, EN, PT, FR, DE, IT
- [x] Dynamic content translation (album names)
- [x] UI copy fully translated
- [x] Error messages localized

---

## 2. KEY FILE MAP

### FRONTEND - Core Files

```
/app/frontend/
├── src/
│   ├── App.js                    # Main app, routing, AuthContext, api client
│   ├── i18n.js                   # All translations (6 languages)
│   ├── index.js                  # React entry point
│   │
│   ├── components/
│   │   ├── UpgradeModal.js       # Plan upgrade modal (Plus/Unlimited)
│   │   ├── SubscriptionSection.js # Plan display, limits, downgrade
│   │   ├── Paywall.js            # Legacy (deprecated, kept for reference)
│   │   └── ui/                   # Shadcn components
│   │
│   ├── pages/
│   │   ├── Login.js              # OTP login flow
│   │   ├── Onboarding.js         # User setup wizard
│   │   ├── Albums.js             # Album list + activation
│   │   ├── AlbumHome.js          # Album detail + stats
│   │   ├── Inventory.js          # Sticker inventory (3 tabs)
│   │   ├── Exchanges.js          # Exchange list (3 tabs)
│   │   ├── ExchangeDetail.js     # Single exchange view
│   │   ├── ExchangeChat.js       # Chat messages
│   │   ├── Matches.js            # Match list
│   │   └── Settings.js           # User settings
│   │
│   └── public/
│       ├── index.html            # HTML template
│       ├── manifest.json         # PWA manifest (to be updated)
│       └── favicon.ico           # App icon
│
├── package.json                  # Dependencies
└── .env                          # REACT_APP_BACKEND_URL
```

### BACKEND - Core Files

```
/app/backend/
├── server.py                     # FastAPI app, all endpoints
├── models.py                     # Pydantic models, plan constants
├── email_service.py              # Resend OTP email
├── requirements.txt              # Python dependencies
├── .env                          # MONGO_URL, RESEND keys, DEV_MODE
│
├── init_albums.py                # Album seed data
├── qatar_stickers.json           # Sticker definitions
│
└── tests/                        # Test files
    ├── test_chat_counting_direct.py
    ├── test_chat_limit_e2e.py
    └── ...
```

### BACKEND - Key Endpoints (server.py)

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/auth/send-otp` | POST | Send OTP email |
| `/api/auth/verify-otp` | POST | Verify OTP, return token |
| `/api/user/plan-status` | GET | Get plan + limits |
| `/api/user/set-plan` | POST | Change plan (MOCKED) |
| `/api/albums` | GET | List all albums |
| `/api/albums/{id}/activate` | POST | Activate album |
| `/api/albums/{id}/deactivate` | POST | Deactivate album |
| `/api/albums/{id}/inventory` | GET | Get user inventory |
| `/api/albums/{id}/inventory` | PUT | Update inventory |
| `/api/albums/{id}/matches` | GET | Get matches |
| `/api/albums/{id}/exchanges` | GET | Get exchanges |
| `/api/albums/{id}/exchanges` | POST | Create exchange |
| `/api/exchanges/{id}` | GET | Get exchange detail |
| `/api/exchanges/{id}/chat` | GET | Get chat messages |
| `/api/exchanges/{id}/chat/messages` | POST | Send message |

---

## 3. SAFETY BACKUP PLAN

### Pre-PWA Conversion Checklist

1. **Git Commit Current State**
   - All current changes are auto-committed by Emergent
   - Current commit represents stable working version

2. **Files NOT to Modify During PWA Conversion**
   - `server.py` - No business logic changes
   - `models.py` - No schema changes
   - `email_service.py` - No auth changes
   - `i18n.js` - No translation key changes
   - `UpgradeModal.js` - No plan logic changes
   - `SubscriptionSection.js` - No subscription logic changes

3. **Files Safe to Modify for PWA**
   - `public/manifest.json` - Add PWA metadata
   - `public/index.html` - Add PWA meta tags
   - `src/index.js` - Add service worker registration
   - New file: `public/sw.js` - Service worker
   - New file: `public/offline.html` - Offline fallback

4. **Rollback Strategy**
   - Use Emergent "Rollback" feature to revert if needed
   - Current checkpoint is stable and tested

### Critical Constants (DO NOT CHANGE)

```python
# models.py
FREE_PLAN_MAX_ALBUMS = 1
FREE_PLAN_MAX_CHATS_PER_DAY = 1
PLUS_PLAN_MAX_ALBUMS = 2
PLUS_PLAN_MAX_CHATS_PER_DAY = 5
```

### Database Collections

| Collection | Purpose |
|------------|---------|
| `users` | User accounts + plan info |
| `albums` | Album templates |
| `stickers` | Sticker definitions |
| `user_album_activations` | Active albums per user |
| `user_inventory` | Sticker ownership |
| `exchanges` | Exchange records |
| `chats` | Chat metadata |
| `chat_messages` | Chat messages |
| `user_reputation` | Reputation tracking |

---

## 4. CURRENT STATUS

| Component | Status |
|-----------|--------|
| Backend | ✅ RUNNING |
| Frontend | ✅ RUNNING |
| MongoDB | ✅ RUNNING |
| Auth/OTP | ✅ WORKING |
| Albums | ✅ WORKING |
| Inventory | ✅ WORKING |
| Exchanges | ✅ WORKING |
| Chat | ✅ WORKING |
| Plan Limits | ✅ WORKING |
| Upgrade Modal | ✅ WORKING |
| Payments | ⚠️ MOCKED |

---

## Ready for PWA Conversion ✓

This document serves as the pre-conversion checkpoint. 
All features are verified working as of this freeze date.
