# AI Email Assistant - Browser Extension

A browser extension that integrates AI-powered email drafting into Gmail and Outlook web interfaces.

## Features

- **One-Click Draft Generation**: Generate email drafts directly in Gmail and Outlook compose windows
- **Personalized Suggestions**: Leverages your past drafts for context-aware writing
- **Tone Control**: Choose from multiple tones (professional, friendly, formal, casual, enthusiastic)
- **Quick Generate**: Generate drafts from the extension popup
- **Usage Tracking**: Monitor your daily usage and quota

## Installation (Development/Staging)

### 1. Prerequisites

- Chrome, Edge, or Firefox browser
- Backend API running (see Backend Setup below)
- API key (staging keys: `demo-key-001` or `test-key-staging`)

### 2. Load Extension

#### Chrome/Edge:
1. Open `chrome://extensions/` (or `edge://extensions/`)
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `browser-extension` folder
5. Extension icon should appear in toolbar

#### Firefox:
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to `browser-extension` folder and select `manifest.json`
4. Extension will be active until browser restart

### 3. Configure Extension

1. Click the extension icon in toolbar
2. Enter API key: `demo-key-001` (staging)
3. Select default tone (e.g., Professional)
4. Click "Save Settings"
5. Verify status shows "Connected" (green dot)

## Backend Setup

### Start Local Backend

```powershell
# Navigate to project root
cd "c:\Users\Merwin\OneDrive\AJ\IK-Capstone-Project\4. Email Generator App\email-generator-app"

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Start server
uvicorn src.api.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

### Update for Railway Deployment

When deploying to Railway, update the API URL:

1. Edit `browser-extension/background/service-worker.js`
2. Change line 2:
   ```javascript
   const API_BASE_URL = 'https://your-railway-app.railway.app/api';
   ```
3. Reload extension in browser

## Usage

### Gmail

1. Open Gmail and click "Compose"
2. (Optional) Add recipient, subject
3. Click the **"✨ AI Draft"** button in the toolbar
4. Draft will be generated and inserted into compose box
5. Review, edit, and send

### Outlook

1. Open Outlook web (outlook.live.com, outlook.office.com, or outlook.office365.com)
2. Click "New message"
3. (Optional) Add recipient, subject
4. Click the **"✨ AI Draft"** button in the toolbar
5. Draft will be generated and inserted
6. Review, edit, and send

### Popup Quick Generate

1. Click extension icon in toolbar
2. Scroll to "Quick Generate" section
3. Enter recipient (optional), subject (optional), and context (required)
4. Click "Generate Draft"
5. Copy generated draft to clipboard

## Staging API Keys

- **demo-key-001**: Unlimited usage, user context: `extension-demo-user`
- **test-key-staging**: Unlimited usage, user context: `staging-tester`

## File Structure

```
browser-extension/
├── manifest.json              # Extension configuration (MV3)
├── background/
│   └── service-worker.js      # API proxy and key management
├── content/
│   ├── gmail-content.js       # Gmail integration
│   ├── outlook-content.js     # Outlook integration
│   └── styles.css             # UI styles for buttons/loaders
├── popup/
│   ├── popup.html             # Extension popup UI
│   ├── popup.css              # Popup styles
│   └── popup.js               # Popup logic
├── icons/
│   ├── icon-16.png            # 16x16 icon
│   ├── icon-48.png            # 48x48 icon
│   └── icon-128.png           # 128x128 icon
└── README.md                  # This file
```

## API Endpoints

Extension uses these backend endpoints:

- **POST** `/api/extension/generate`: Generate email draft
  - Headers: `X-Extension-Key: <api-key>`
  - Body: `{ recipient, subject, body_context, tone }`
  - Response: `{ draft, word_count, tone, intent, similar_used, metadata }`

- **GET** `/api/extension/usage`: Check usage stats
  - Headers: `X-Extension-Key: <api-key>`
  - Response: `{ drafts_today, quota_remaining }`

- **GET** `/api/extension/health`: Health check
  - Response: `{ status, version }`

## Troubleshooting

### Button Not Appearing

- **Gmail**: Wait for compose box to fully load (3-5 seconds)
- **Outlook**: Ensure you're on a supported Outlook domain
- **Check Console**: Open DevTools (F12) → Console tab → look for errors

### "API Key Invalid" Error

- Verify key is saved: Click extension icon → Settings → check API Key field
- Ensure backend is running: Open `http://localhost:8000/api/extension/health`
- Try re-entering key: Use `demo-key-001` or `test-key-staging`

### "Failed to Generate" Error

- Check backend logs for errors
- Verify CORS is configured for extension origins
- Ensure Gemini API key is set in backend `.env`

### Status Shows "Disconnected"

- Backend may not be running: Start with `uvicorn src.api.main:app --reload`
- Wrong URL: Check service-worker.js `API_BASE_URL` matches your backend
- Network error: Check browser console for fetch errors

## Development

### Test Content Scripts

```javascript
// Open Gmail/Outlook compose
// Open DevTools console
// Check for logs:
"AI Draft button injected" // Success
"Compose box not found"     // Waiting for compose
```

### Test Service Worker

```javascript
// Open chrome://extensions/ → Extension details → Service Worker → Inspect
// Check console for:
"Extension installed"       // On install
"Generating draft..."       // On generate request
```

### Modify Styles

Edit `content/styles.css` and reload extension to see changes immediately.

## Next Steps (Production)

1. **Icons**: Replace placeholder icons with professional designs (16/48/128px)
2. **CORS**: Add `chrome-extension://*` and `moz-extension://*` to backend CORS origins
3. **API Key Management**: Implement database-backed key storage and rotation
4. **Usage Quotas**: Enforce rate limits per API key
5. **Store Submission**: Submit to Chrome Web Store ($5 fee), Firefox Add-ons, Edge Add-ons
6. **Privacy Policy**: Host privacy policy for store listing
7. **Monitoring**: Add Sentry or similar for error tracking
8. **Domain**: Use custom domain with SSL for production backend

## Version

**1.0.0 - Staging** (November 2025)

## License

Internal use only - not for public distribution.
