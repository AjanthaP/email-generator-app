# Extension Testing Guide

Quick guide to test the AI Email Assistant browser extension in staging mode.

## Prerequisites Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Gemini API key configured in `.env` file
- [ ] Chrome, Edge, or Firefox browser

## Step 1: Start Backend Server

```powershell
# Navigate to project root
cd "c:\Users\Merwin\OneDrive\AJ\IK-Capstone-Project\4. Email Generator App\email-generator-app"

# Activate virtual environment (if not active)
.\venv\Scripts\Activate.ps1

# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Server should start at: http://localhost:8000
# Check health: http://localhost:8000/health
# API docs: http://localhost:8000/docs
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

## Step 2: Verify Backend Endpoints

Open browser and test:

1. **Health Check**: http://localhost:8000/health
   - Should return: `{"status":"ok","app_name":"AI Email Assistant","version":"1.0.0"}`

2. **Extension Health**: http://localhost:8000/api/extension/health
   - Should return: `{"status":"healthy","version":"1.0.0"}`

3. **API Docs**: http://localhost:8000/docs
   - Should show interactive API documentation

## Step 3: Load Extension (Chrome/Edge)

1. Open Chrome and navigate to: `chrome://extensions/`
   - Or Edge: `edge://extensions/`

2. Enable **Developer mode** (toggle in top-right corner)

3. Click **"Load unpacked"**

4. Navigate to and select:
   ```
   C:\Users\Merwin\OneDrive\AJ\IK-Capstone-Project\4. Email Generator App\email-generator-app\browser-extension
   ```

5. Extension should appear in list with:
   - Name: **AI Email Assistant**
   - Version: **1.0.0**
   - Status: **Enabled**

6. Pin extension to toolbar (click puzzle icon → pin)

## Step 4: Configure Extension

1. Click extension icon in toolbar

2. In popup, enter settings:
   - **API Key**: `demo-key-001`
   - **Default Tone**: `Professional`

3. Click **"Save Settings"**

4. Verify:
   - Status indicator shows **green dot** and **"Connected"**
   - Save status shows **"✓ Settings saved successfully!"**

5. Check usage stats:
   - **Drafts Today**: Should show `0`
   - **Quota Remaining**: Should show `Unlimited`

## Step 5: Test in Gmail

1. Open Gmail: https://mail.google.com

2. Click **"Compose"** to open new email

3. Wait 2-3 seconds for compose box to load

4. Look for **"✨ AI Draft"** button in toolbar (near formatting buttons)

### Test Case A: Full Context

1. Fill in:
   - **To**: `colleague@example.com`
   - **Subject**: `Project Update Meeting`
   - **Body**: Leave empty or add brief context

2. Click **"✨ AI Draft"** button

3. Verify:
   - Loading spinner appears (2-5 seconds)
   - Draft text is inserted into compose box
   - Success toast appears (green, bottom-right)
   - Draft is contextually relevant to recipient/subject

### Test Case B: Subject Only

1. Clear compose box (close and reopen)

2. Fill in:
   - **To**: Leave empty
   - **Subject**: `Thank you for the presentation`
   - **Body**: Leave empty

3. Click **"✨ AI Draft"**

4. Verify:
   - Draft generates based on subject
   - Tone is professional
   - Content is appropriate

### Test Case C: Minimal Context

1. Clear compose box

2. Fill in:
   - **To**: Leave empty
   - **Subject**: Leave empty
   - **Body**: Type: `Schedule a meeting next week`

3. Click **"✨ AI Draft"**

4. Verify:
   - Draft generates from body context
   - Appropriate greeting and closing

## Step 6: Test in Outlook

1. Open Outlook: https://outlook.live.com or https://outlook.office.com

2. Click **"New message"**

3. Look for **"✨ AI Draft"** button in toolbar

4. Repeat Test Cases A, B, C from Gmail section

5. Verify:
   - Button appears in Outlook toolbar
   - Draft insertion works correctly
   - UI feedback (loading, success, error) displays

## Step 7: Test Popup Quick Generate

1. Click extension icon in toolbar

2. Scroll to **"Quick Generate"** section

3. Fill in:
   - **To**: `manager@example.com` (optional)
   - **Subject**: `Weekly Status Report` (optional)
   - **Context**: `Summarize project progress and next steps`

4. Click **"Generate Draft"**

5. Verify:
   - Button shows "Generating..." state
   - Draft appears in green success box
   - "Copy to Clipboard" button works
   - Usage stats update (Drafts Today increments)

## Step 8: Test Error Handling

### Invalid API Key

1. Click extension icon → Settings
2. Change API Key to: `invalid-key-123`
3. Click "Save Settings"
4. Status should show **red dot** and **"Disconnected"**
5. Try generating draft → should show error message

### Backend Offline

1. Stop backend server (CTRL+C in terminal)
2. Try generating draft in Gmail
3. Verify error toast appears: "Failed to generate draft"
4. Restart backend and verify it works again

### Empty Context

1. Open Gmail compose (empty)
2. Click "✨ AI Draft" without any input
3. Should show error: "Please provide some context"

## Troubleshooting

### Button Not Appearing

**Gmail:**
- Hard refresh page (CTRL+SHIFT+R)
- Open DevTools console (F12) → check for errors
- Wait longer (compose box can take 5-10 seconds to fully load)

**Outlook:**
- Try different Outlook domain (outlook.live.com vs outlook.office.com)
- Check DevTools console for selector errors

### API Call Failing

1. Check backend is running: http://localhost:8000/health
2. Check browser console (F12) for CORS errors
3. Verify API key in extension settings
4. Check service worker console:
   - chrome://extensions/ → Extension details → Service Worker → Inspect

### CORS Errors

If you see CORS errors in console:
```
Access to fetch at 'http://localhost:8000/api/extension/generate' from origin 'chrome-extension://...' has been blocked by CORS policy
```

**Fix:**
- Backend CORS is already configured for `chrome-extension://*` and `moz-extension://*`
- Restart backend server to apply changes
- Hard refresh extension (chrome://extensions/ → reload button)

## Expected Behavior Summary

✅ **Should Work:**
- Button appears in Gmail/Outlook compose
- Draft generates in 2-5 seconds
- Draft is contextually relevant
- Loading/success/error UI displays correctly
- Popup quick generate works
- Usage stats update

❌ **Should Show Error:**
- Invalid API key → "API key invalid"
- Backend offline → "Failed to generate"
- Empty context → "Please provide context"
- Network error → "An error occurred"

## Next Steps After Testing

Once staging tests pass:

1. **Deploy to Railway**:
   - Push code to GitHub
   - Connect Railway to repository
   - Set environment variables (GEMINI_API_KEY, DATABASE_URL)
   - Update service-worker.js with Railway URL

2. **Update Extension for Production**:
   - Change `API_BASE_URL` in service-worker.js
   - Replace placeholder icons
   - Update manifest version

3. **Store Submission**:
   - Chrome Web Store ($5 registration)
   - Firefox Add-ons (free)
   - Edge Add-ons (free)

## Test Results Checklist

After testing, verify all items:

- [ ] Backend starts without errors
- [ ] Health endpoints respond correctly
- [ ] Extension loads in browser
- [ ] API key saves successfully
- [ ] Status shows "Connected"
- [ ] Gmail button appears
- [ ] Gmail draft generation works
- [ ] Outlook button appears
- [ ] Outlook draft generation works
- [ ] Popup quick generate works
- [ ] Usage stats display correctly
- [ ] Error handling works (invalid key, backend offline, empty context)
- [ ] CORS configured correctly (no console errors)

## Contact

For issues or questions during testing, check:
- Backend logs in terminal
- Browser DevTools console (F12)
- Extension service worker console (chrome://extensions/)

---

**Last Updated**: November 23, 2025
**Version**: 1.0.0 - Staging
