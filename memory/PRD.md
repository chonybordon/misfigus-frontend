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

### Internationalization (i18n)
- **Supported Languages**: Spanish (es), English (en), Portuguese (pt), French (fr), German (de), Italian (it)
- **Default Language**: Spanish (es)
- **Fallback Chain**: Selected language → Spanish → English
- Language selection as first step of onboarding

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
- In-app chat for exchange coordination
- Exchange confirmation with success/failure reporting
- Reputation system (trusted, under review, restricted)

### Freemium Model
- **Free Plan**: 1 active album, 1 trade match per day
- **Premium Plan**: Unlimited albums and trades
- Paywall UI when limits hit (MOCKED - no real payment integration)

## Technical Architecture

### Frontend
- React with react-router-dom
- Shadcn/UI components
- i18next for internationalization
- Tailwind CSS

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
- Real payment integration for Premium upgrade
- Push notifications for new matches/messages
- Album sharing via deep links
- Statistics/analytics dashboard
