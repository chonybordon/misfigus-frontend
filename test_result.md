# Test Result Documentation

## Current Test Focus: Exchange Lifecycle and Reputation System

### Features to Test:

1. **Exchange Creation (POST /api/albums/{albumId}/exchanges)**
   - Only allowed for users with mutual sticker matches
   - Creates exchange record with status=pending
   - Creates chat for the exchange
   - Adds system message to chat

2. **Exchange Confirmation (POST /api/exchanges/{exchangeId}/confirm)**
   - User can confirm with thumbs up (confirmed=true) or thumbs down (confirmed=false)
   - Thumbs down requires failure_reason
   - Both users confirming thumbs up → status=completed
   - Either user thumbs down → status=failed
   - Updates user reputation automatically

3. **Reputation System**
   - Successful exchange: no negative effect
   - Failed exchange: increments failed_exchanges and consecutive_failures
   - 2 consecutive failures → under_review status + 48h invisibility
   - 5 total failures → restricted status (suspended)
   - Restricted users cannot appear in matches or create exchanges

4. **Chat System (only for pending exchanges)**
   - GET /api/exchanges/{exchangeId}/chat returns messages
   - POST /api/exchanges/{exchangeId}/chat/messages - only allowed if status=pending
   - After completion/failure, chat becomes read-only

### Test Users:
- exchange-test-user-1 (has duplicates of stickers 1-5)
- exchange-test-user-2 (has duplicates of stickers 6-10)
- Qatar album: bc32fecb-f640-4d00-880d-5043bc112d4b

### Test Scenarios:
1. Create exchange between user1 and user2
2. Send chat message
3. User1 confirms thumbs up
4. User2 confirms thumbs up → status should become completed
5. Verify reputation updated for both users
6. Verify chat becomes read-only after completion

### Expected Results:
- Exchange creation returns exchange ID
- Chat messages can be sent while pending
- Confirmation updates status correctly
- Reputation is computed automatically
