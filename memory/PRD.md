# MisFigus - Sticker Trading App PRD

## Overview
MisFigus is a sticker trading platform that allows collectors to manage their sticker albums, track duplicates/missing stickers, and find nearby traders for in-person exchanges.

## Core User Personas
- **Sticker Collectors**: Users who collect stickers for various albums (sports, anime, etc.)
- **Traders**: Users looking to exchange duplicate stickers with others nearby

## Core Requirements

### Authentication
- OTP-based email authentication via Resend
- No password required - magic link style login
- **Email normalization**: All emails are trimmed and lowercased to prevent duplicate users
- **Single point of user creation**: Users are ONLY created during OTP verification (not during OTP send)
- **Unique index** on email field to enforce uniqueness at DB level

### Internationalization (i18n)
- **Supported Languages**: Spanish (es), English (en), Portuguese (pt), French (fr), German (de), Italian (it)
- **Default Language**: Spanish (es)
- **Fallback Chain**: Selected language → Spanish → English
- Language selection as first step of onboarding
- **i18n-driven album names**: Albums use `name_key` field to look up translations
- **i18n-driven categories**: Albums use `category_key` field for category translations
- **Legal disclaimer**: Fan-made collection disclaimer translated in all 6 languages

### User Profile
- Display name, email, location (country/city/neighborhood)
- Search radius configuration (3, 5, 10, 15, 20 km)
- Terms & Conditions acceptance tracking
- Location/radius change cooldowns (7 days for both)

### Albums & Inventory
- Multiple album support with activation system
- Sticker tracking: owned, missing, duplicates
- Progress tracking per album

### Trading System
- Location-based match finding
- In-app chat for exchange coordination with **real-time polling (2s interval)**
- Exchange confirmation with success/failure reporting
- **Dynamic reputation system**:
  - "Nuevo" (🔵) → 0 successful exchanges
  - "Confiable" (🟢) → 3+ successful exchanges, no serious failures
  - "Con observaciones" (🟡) → any serious failure
  - "Restringido" (🔴) → 5+ serious failures (suspended)

### Subscription Plans (3-Tier System)

| Plan | Albums | Chats/Day | Messages | Ads |
|------|--------|-----------|----------|-----|
| **Gratuito** | 1 | 1 | Unlimited | Yes |
| **Plus** (Recommended) | 2 | 5 | Unlimited | No |
| **Ilimitado** | ∞ | ∞ | Unlimited | No |

- Plan types: Monthly (30 days), Annual (365 days)
- Subscription management UI in Settings with:
  - Current plan badge (color-coded: gray/blue/purple)
  - Usage counters (albums X/N, chats X/N)
  - Upgrade dialog showing Plus and Unlimited options
  - Downgrade blocked if albums exceed target plan limit
- Paywall UI when limits hit (MOCKED - no real payment integration)
- **Chat limit enforcement**: "Alcanzaste el límite de tu versión gratuita. Pasá a Premium para iniciar más chats."
- **Unlimited messages**: Once a chat is started, messaging is unlimited
- **i18n**: All plan labels translated in all 6 languages

### Inventory UX
- **3 tabs only**: "Mi inventario" (editable), "Faltan" (read-only, red styling), "Duplicados" (read-only, yellow styling)
- Editing (+/- buttons) only available in "Mi inventario" tab

### Exchanges UX
- Default tab is "New exchanges" (not "Active")
- 3-tab navigation: "Nuevos intercambios" | "Activos" | "Completados"
- **Direct navigation**: Clicking a match goes directly to Exchange Detail (no intermediate screen)
- Flow: Exchanges (New tab) → Click match → Exchange Detail + Chat

## Technical Architecture

### Frontend
- React with react-router-dom
- Shadcn/UI components
- i18next for internationalization
- Tailwind CSS
- **Mobile-first responsive design** - tested at 360px, 390px, 430px viewports

### Backend
- FastAPI (Python)
- MongoDB database

### Third-Party Integrations
- **Resend**: OTP email delivery
- **react-markdown**: Terms & Conditions rendering

## What's Been Implemented

### December 2024
- Full authentication flow with OTP
- Multi-step onboarding (language → name → location → terms)
- Album management with activation/deactivation
- Inventory management (owned, missing, duplicates)
- Trade matching and exchange flow
- In-app chat system
- Freemium gating logic

### January 2025
- Full i18n support for 6 languages
- Spanish as default language with proper fallbacks
- **Profile Screen Translations**: Complete translations for all profile-related keys across all 6 languages
- Database reset for production readiness
- Trade flow logic fixes
- **Comprehensive Duplicate User Fix**: Email normalization, unique DB index, data cleanup scripts
- **Subscription Management UI**: View/manage plans in Settings (Free vs Premium)
- **Full Mobile Responsive UI Overhaul**: Layout, spacing, overflow fixes across all pages
- **Dynamic Reputation System**: "Nuevo" (0 exchanges), "Confiable" (3+ exchanges)
- **Real-time Chat Polling**: Auto-refresh messages without manual refresh
- **3-Tab Navigation for Exchanges**: "Nuevos intercambios" | "Activos" | "Completados"
  - Icons: Search (magnifying glass), MessageCircle (chat), Archive (box)
  - Default tab: Active (if exchanges exist) or New exchanges
  - Badges: Green badge on New (if matches), Red pulsing badge on Active (if unread)

## Profile Translation Keys (Implemented)
All the following keys are now translated in all 6 languages:
- `profile.title`, `profile.basicInfo`, `profile.displayName`, `profile.displayNamePlaceholder`
- `profile.email`, `profile.save`, `profile.saved`, `profile.helperText`
- `profile.locationTitle`, `profile.locationDescription`, `profile.location`
- `profile.searchRadius`, `profile.setLocation`, `profile.changeLocation`, `profile.changeRadius`
- `profile.noLocationSet`, `profile.locationCooldown`, `profile.radiusCooldown`
- `profile.locationUpdated`, `profile.radiusUpdated`, `profile.changeRadiusDescription`
- `profile.selectRadius`, `profile.locationPrivacyNote`, `profile.locationRequired`
- `profile.locationRequiredDesc`, `profile.setupLocation`, `profile.setupLocationDesc`
- `profile.country`, `profile.selectCountry`, `profile.city`, `profile.searchCity`
- `profile.selectCity`, `profile.citySearchHelp`, `profile.neighborhood`
- `profile.neighborhoodPlaceholder`, `profile.neighborhoodHelp`
- `profile.termsTitle`, `profile.termsAccepted`, `profile.termsVersion`
- `profile.termsAcceptedAt`, `profile.viewTerms`

## Known Limitations
- **Premium Upgrade**: The "Upgrade" button on the paywall is MOCKED (no Stripe/payment integration)
- Dates use browser's `toLocaleDateString()` for locale-friendly formatting

## Trademark Cleanup (January 2025)
All trademarked content has been replaced with legally safe, generic alternatives:

### Album Name Changes
| Old Name | New Name |
|----------|----------|
| FIFA World Cup Qatar 2022 | Álbum Mundial de Fútbol 2022 |
| FIFA World Cup 2026 | Álbum Mundial de Fútbol 2026 |
| Pokémon | Criaturas Fantásticas |
| Dragon Ball | Guerreros del Anime |
| Marvel | Héroes del Multiverso |
| Disney | Personajes Animados |

### Sticker Label Changes (Football Albums)
| Old Label | New Label |
|-----------|-----------|
| FWC 2022 Logo | Emblema del Torneo |
| World Cup Trophy | Trofeo del Campeonato |
| Qatar 2022 | Evento 2022 |
| [Country] Badge | Emblema de [País] |
| FIFA (team) | Torneo |

### Legal Disclaimer
A fan-made disclaimer is displayed on the album detail page in all 6 languages.

## File Structure
```
/app
├── backend/
│   ├── models.py       # User, Album, Exchange schemas
│   └── server.py       # FastAPI endpoints
└── frontend/
    └── src/
        ├── components/ui/  # Shadcn components
        ├── pages/
        │   ├── Profile.js    # User profile management
        │   ├── Settings.js   # Language switcher
        │   ├── Albums.js     # Album listing
        │   └── Onboarding.js # New user setup
        ├── App.js            # Main app with routing
        └── i18n.js           # All UI translations (6 languages)
```

## Pending/Future Tasks
- **P1**: Real payment integration for Premium upgrade (Stripe) - subscription system is currently MOCKED
- Push notifications for new matches/messages
- Album sharing via deep links
- Statistics/analytics dashboard
- App packaging for Android / iOS

## Upgrade Modal UX (Completed January 2025)
The "Upgrade Plan" modal has been enhanced with the following UX improvements:
- **Plan Labels**: Display "Plus" and "Unlimited" (removed redundant "Plan" prefix)
- **No Preselection**: Modal opens with no plan selected by default
- **Disabled CTA**: Upgrade button is grayed out until a plan is selected
- **Dynamic Button**: 
  - Plus selection: Blue gradient button with "Upgrade to Plus" text
  - Unlimited selection: Purple gradient button with "Upgrade to Unlimited" text
- **Visual Highlighting**: Selected plan card has colored border and checkmark indicator
- **Full i18n Support**: All labels translated in all 6 languages

## Exchange Tabs Feature (Completed January 2025)
The "My Exchanges" screen now has a 3-tab navigation system:
- **Tab 1: "Nuevos intercambios" (New exchanges)**: Shows available matches for trading
- **Tab 2: "Activos" (Active)**: Shows ongoing exchanges with chat
- **Tab 3: "Completados" (Completed)**: Shows exchange history

### Tab Labels by Language
| Language | Tab 1 | Tab 2 | Tab 3 |
|----------|-------|-------|-------|
| Spanish (es) | Nuevos intercambios | Activos | Completados |
| English (en) | New exchanges | Active | Completed |
| Portuguese (pt) | Novas trocas | Ativos | Concluídos |
| French (fr) | Nouveaux échanges | Actifs | Terminés |
| German (de) | Neue Tausche | Aktiv | Abgeschlossen |
| Italian (it) | Nuovi scambi | Attivi | Completati |
