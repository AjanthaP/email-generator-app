# Google OAuth Setup Guide for Extension

The extension now supports Google OAuth to automatically fetch your real profile info (name, email, signature).

## Setup Steps (Required for Production)

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your Project ID

### 2. Enable Gmail API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Gmail API" and enable it
3. Search for "Google+ API" and enable it (for profile info)

### 3. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Chrome Extension**
4. Name: `AI Email Draft Generator`
5. Item ID: Get this from chrome://extensions (your extension ID after loading)
6. Click **Create**
7. Copy the **Client ID** (format: `xxxxx.apps.googleusercontent.com`)

### 4. Update Extension Manifest

Edit `browser-extension/manifest.json`:

```json
"oauth2": {
  "client_id": "YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com",
  "scopes": [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly"
  ]
}
```

Replace `YOUR_ACTUAL_CLIENT_ID` with your real Client ID.

### 5. Reload Extension

1. Go to chrome://extensions
2. Click **Reload** on your extension
3. First time generating a draft will trigger OAuth consent screen

## What the OAuth Flow Does

When you generate your first draft:
1. Extension requests Google sign-in (one-time consent)
2. Fetches your:
   - Email address (used as user_id)
   - Full name (for personalization)
   - Gmail signature (from settings)
3. Caches this info for future requests
4. Backend auto-creates your profile with real data

## Staging Mode (Without OAuth)

If you don't set up OAuth, the extension falls back to:
- Extracting email from Gmail DOM (less reliable)
- Extracting signature from compose box
- Using "User" as default name

## Testing OAuth

After setup:
```powershell
# Reload backend
.\start-extension-test.ps1

# In Chrome:
# 1. Reload extension (chrome://extensions)
# 2. Open Gmail compose
# 3. Click "AI Draft" button
# 4. First time: OAuth consent screen appears
# 5. Approve permissions
# 6. Generate draft - should use your real name!
```

Check console for:
```
[AI Draft][BG] Profile fetched: your.email@gmail.com Your Name
```

## Troubleshooting

**"Chrome identity API not available"**
- Check `manifest.json` has `"identity"` permission
- Ensure OAuth client_id is set correctly

**OAuth consent screen doesn't appear**
- Make sure Gmail API is enabled in Google Cloud
- Verify extension ID matches the one in OAuth credentials
- Try removing and re-adding extension

**Still shows "User"**
- Check browser console for auth errors
- Verify backend received sender_name in logs
- Check `src/memory/user_profiles.json` for your email key

## Privacy Note

The extension only requests:
- Email address (to identify your profile)
- Profile name (for signatures)
- Gmail read-only (to fetch signature from settings)

No emails are read or stored. Signature is cached locally.
