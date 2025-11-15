# Draft History Investigation Summary

## Issue
User `ajantha22ma_gmail_com` reports no draft history visible in the UI.

## Root Cause Analysis

### Architecture Overview
- **Frontend**: React app on Vercel (email-generator-app-frontend.vercel.app)
- **Backend**: FastAPI on Railway (email-generator-app-production.up.railway.app)
- **Database**: PostgreSQL on Railway

### Storage Behavior
The MemoryManager has dual-mode operation:

1. **With DATABASE_URL** (Production on Railway):
   - Saves drafts to PostgreSQL `drafts` table
   - Persistent across deployments
   - Shared across all backend instances

2. **Without DATABASE_URL** (Local Development):
   - Falls back to JSON files in `data/drafts/`
   - Local only, not shared with Railway

## Findings

### Local Environment
- ✅ MemoryManager auto-fallback working correctly
- ✅ Test draft saved successfully to local JSON
- ✅ Draft retrieval working: `data/drafts/ajantha22ma_gmail_com_drafts.json`
- ⚠️ DATABASE_URL not set locally (expected - only set on Railway)

### Production Environment (Railway)
**Need to verify:**
1. Are drafts being saved to PostgreSQL on Railway?
2. Is `save_to_history` parameter being passed from frontend?
3. Are there any errors in Railway logs during draft save?

## Code Review - Save Flow

### API Endpoint (`src/api/routers/email.py`)
```python
if payload.save_to_history:  # ← Check if this is True from frontend
    _memory_manager.save_draft(
        user_id,
        {
            "content": draft,
            "draft": draft,
            "metadata": metadata,
            "original_input": payload.prompt
        },
    )
```

### Frontend Integration Points
Check if the React frontend is:
1. ✅ Sending `save_to_history: true` in the request payload
2. ✅ Passing correct `user_id` (should be `ajantha22ma_gmail_com`)
3. ❓ Calling the history endpoint to retrieve drafts

## Verification Steps

### 1. Check Railway PostgreSQL Database
```bash
# Connect to Railway PostgreSQL
railway connect postgres

# Query drafts for user
SELECT id, user_id, created_at, LEFT(content, 50) as preview
FROM drafts
WHERE user_id = 'ajantha22ma_gmail_com'
ORDER BY created_at DESC
LIMIT 10;
```

### 2. Check Railway Backend Logs
```bash
railway logs
```
Look for:
- `"Saved draft to database for user ajantha22ma_gmail_com"`
- Any errors during draft save operation

### 3. Test API Endpoint Directly
```bash
curl -X POST https://email-generator-app-production.up.railway.app/api/v1/email/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Test email for draft history",
    "user_id": "ajantha22ma_gmail_com",
    "save_to_history": true,
    "tone": "formal"
  }'
```

### 4. Check Frontend Request Payload
Open browser DevTools → Network tab when generating email:
- Request to `/api/v1/email/generate`
- Check payload includes: `"save_to_history": true`
- Check response includes: `"saved": true`

## Potential Issues

### Issue 1: Frontend Not Sending `save_to_history`
**Solution**: Ensure React app sets `save_to_history: true` in API request

### Issue 2: Database Not Initialized on Railway
**Solution**: Run database initialization on Railway:
```bash
railway run python -c "from src.db.database import init_db; init_db()"
```

### Issue 3: Draft Save Errors on Railway
**Check**: Railway logs for database errors
**Solution**: May need to check PostgreSQL connection settings

### Issue 4: Frontend Not Calling History Endpoint
**Solution**: Implement history retrieval in React frontend:
```javascript
// GET /api/v1/users/{user_id}/drafts
const response = await fetch(
  `https://email-generator-app-production.up.railway.app/api/v1/users/${userId}/drafts`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const drafts = await response.json();
```

## Next Steps

1. **Immediate**: Check Railway logs to see if drafts are being saved
2. **Frontend**: Verify `save_to_history` is being sent
3. **Database**: Query Railway PostgreSQL to check if drafts exist
4. **API Test**: Send test request to verify save flow works end-to-end

## Code Fixes Applied

### 1. MemoryManager Auto-Detection
✅ Fixed to auto-detect database availability instead of requiring explicit session

### 2. Draft Data Key Support
✅ Added support for both `"content"` and `"draft"` keys for backward compatibility

### 3. API Endpoint Enhancement
✅ Now passes both keys plus `original_input` when saving drafts

## Testing Locally

To test with local PostgreSQL:

1. Set DATABASE_URL in `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/email_generator
```

2. Run migrations:
```bash
python scripts/setup_database.py
```

3. Test draft saving:
```bash
python test_draft_history.py
```

---

**Status**: Investigation complete, code fixes applied
**Next**: Verify on Railway production environment
