# OAuth Setup Checklist - Fix CORS and Login Issues

## Current Issue
- CORS errors on `/api/auth/exchange`
- 500 Internal Server Error during OAuth callback

## Root Causes
1. Railway environment variables not set correctly
2. Google OAuth redirect URI mismatch
3. Backend not deployed with latest CORS fixes

---

## ✅ Step-by-Step Fix

### 1. Railway Environment Variables

Set these **exact** values in Railway (Variables tab):

```bash
# Frontend URL
FRONTEND_URL=https://email-generator-app-frontend.vercel.app

# CORS Origins (comma-separated, NO brackets, NO extra quotes)
CORS_ORIGINS=https://email-generator-app-frontend.vercel.app,http://localhost:5173,http://localhost:3000

# Google OAuth Redirect URI (must match Google Console)
GOOGLE_REDIRECT_URI=https://email-generator-app-frontend.vercel.app

# Google OAuth Credentials (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
ENABLE_GOOGLE_OAUTH=true

# Gemini API (required for email generation)
GEMINI_API_KEY=your_gemini_api_key_here
```

**Important formatting notes:**
- For `CORS_ORIGINS`: Use comma-separated values, NO surrounding quotes or brackets
- Railway auto-wraps values, so paste the raw string directly
- DO NOT use JSON array format like `["url1","url2"]` - use `url1,url2`

---

### 2. Google Cloud Console Setup

1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add **exactly**:
   ```
   https://email-generator-app-frontend.vercel.app
   ```
4. Remove any old redirect URIs pointing to backend or localhost (unless needed for local dev)
5. Click **Save**

---

### 3. Verify Backend Deployment

After setting env vars, Railway should auto-redeploy. Verify:

**Check deployment logs:**
```bash
# Look for this line in Railway logs:
[startup] CORS allow_origins resolved: ['https://email-generator-app-frontend.vercel.app', ...]
```

**Test CORS manually:**
```powershell
# PowerShell command to verify CORS
$headers = @{ Origin = "https://email-generator-app-frontend.vercel.app" }
Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/health" -Headers $headers | Select-Object -ExpandProperty Headers
```

Should see:
```
Access-Control-Allow-Origin: https://email-generator-app-frontend.vercel.app
Access-Control-Allow-Credentials: true
```

---

### 4. Test OAuth Flow

**Test start endpoint:**
```powershell
$response = Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/api/auth/start" -Method POST -ContentType "application/json" -Body '{"provider":"google"}'
$json = $response.Content | ConvertFrom-Json
$json.authorization_url
```

The `authorization_url` should contain:
```
redirect_uri=https://email-generator-app-frontend.vercel.app
```

If it still shows the backend URL, the env var didn't update yet.

---

## How OAuth Flow Works (Option B - SPA Flow)

1. User clicks "Sign in with Google" in frontend
2. Frontend calls `POST /api/auth/start` → gets Google authorization URL
3. User redirected to Google login
4. Google redirects back to: `https://email-generator-app-frontend.vercel.app?code=XXX&state=YYY`
5. Frontend reads `code` and `state` from URL
6. Frontend calls `POST /api/auth/exchange` with `{ provider, code, state }`
7. Backend exchanges code for token (server-side, secure)
8. Backend returns user info + session
9. Frontend saves session and shows logged-in state

---

## Common Mistakes

❌ **Wrong:** Setting `CORS_ORIGINS=["https://..."]` (JSON array)
✅ **Right:** Setting `CORS_ORIGINS=https://email-generator-app-frontend.vercel.app,http://localhost:5173`

❌ **Wrong:** Google redirect URI = backend URL
✅ **Right:** Google redirect URI = frontend URL (for SPA flow)

❌ **Wrong:** Adding extra quotes around Railway env values
✅ **Right:** Paste raw value directly (Railway handles quoting)

---

## Verification Commands

After setup, run these to verify everything:

```powershell
# 1. Health check with CORS
$h = @{ Origin = "https://email-generator-app-frontend.vercel.app" }
(Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/health" -Headers $h).Headers["Access-Control-Allow-Origin"]

# 2. Auth providers
Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/api/auth/providers" -Headers $h

# 3. Start OAuth (check redirect_uri in response)
$r = Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/api/auth/start" -Method POST -ContentType "application/json" -Body '{"provider":"google"}' -Headers $h
($r.Content | ConvertFrom-Json).authorization_url
```

All should return proper CORS headers and the redirect_uri should point to your frontend.

---

## Still Not Working?

1. **Check Railway logs** for errors or the startup log showing CORS origins
2. **Clear browser cache** and try in incognito mode
3. **Check Vercel deployment** - ensure frontend has latest code
4. **Verify Google credentials** are correct in Railway
5. **Check Network tab** in browser DevTools to see actual request/response headers

---

## Latest Code Changes

✅ Added catch-all exception handler for 500 errors (includes CORS headers)
✅ Improved error handling in OAuth exchange endpoint
✅ Added startup log showing resolved CORS origins
✅ Frontend already uses `POST /api/auth/exchange` (SPA-friendly)

**All changes pushed to master** - Railway should auto-deploy.
