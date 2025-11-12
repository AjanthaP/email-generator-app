# Frontend Deployment Guide

## Overview

The frontend is a **React + Vite** application that connects to the FastAPI backend via REST API.

**Frontend Stack:**
- React 19.2.0
- TypeScript
- Vite 7.2.2
- No server-side rendering (static build)

---

## Deployment Options

### Option 1: Vercel (Recommended - Easiest) ⭐

**Why Vercel?**
- ✅ Optimized for Vite/React
- ✅ Free tier with generous limits
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Automatic deployments from Git

**Steps:**

1. **Install Vercel CLI** (optional, can use web dashboard)
   ```bash
   npm i -g vercel
   ```

2. **Deploy via CLI:**
   ```bash
   cd frontend
   vercel
   ```
   
   Follow the prompts:
   - Project name: `email-generator-frontend`
   - Framework: `Vite` (auto-detected)
   - Build command: `npm run build`
   - Output directory: `dist`

3. **Set Environment Variable in Vercel Dashboard:**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add:
     ```
     VITE_API_BASE_URL = https://your-backend.up.railway.app
     ```

4. **Deploy to Production:**
   ```bash
   vercel --prod
   ```

**OR Deploy via Web Dashboard:**
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Set root directory to `frontend`
4. Add environment variable `VITE_API_BASE_URL`
5. Deploy!

---

### Option 2: Netlify

**Steps:**

1. **Install Netlify CLI** (optional)
   ```bash
   npm i -g netlify-cli
   ```

2. **Deploy via CLI:**
   ```bash
   cd frontend
   netlify deploy
   ```

3. **Set Environment Variable:**
   - Netlify Dashboard → Site Settings → Environment Variables
   - Add: `VITE_API_BASE_URL = https://your-backend.up.railway.app`

4. **Deploy to Production:**
   ```bash
   netlify deploy --prod
   ```

**OR Deploy via Web Dashboard:**
1. Go to https://app.netlify.com/start
2. Connect GitHub repository
3. Set base directory to `frontend`
4. Build command: `npm run build`
5. Publish directory: `dist`
6. Add environment variable `VITE_API_BASE_URL`

---

### Option 3: Railway (Keep Everything Together)

Deploy frontend as a separate Railway service in the same project.

**Steps:**

1. **In Railway Dashboard:**
   - Go to your existing project
   - Click **"New Service"** → **"GitHub Repo"**
   - Select the same `email-generator-app` repository
   
2. **Configure Service:**
   - Click on the new service → **Settings**
   - Set **Root Directory** = `frontend`
   - Railway will auto-detect `railway.toml`

3. **Add Environment Variable:**
   - Go to **Variables** tab
   - Add:
     ```
     VITE_API_BASE_URL = ${{YOUR_BACKEND_SERVICE.RAILWAY_PUBLIC_DOMAIN}}
     ```
   - Or manually set:
     ```
     VITE_API_BASE_URL = https://your-backend.up.railway.app
     ```

4. **Deploy:**
   - Railway will automatically build and deploy
   - Uses `frontend/railway.toml` configuration

**Railway Configuration (already created):**
```toml
# frontend/railway.toml
[build]
command = "npm install && npm run build"
publish = "dist"

[build.environment]
NODE_VERSION = "18"
```

---

## Post-Deployment Steps

After deploying the frontend, update your backend configuration:

### 1. Update Backend CORS Settings

In Railway Dashboard → Backend Service → Variables, update:

```bash
CORS_ORIGINS=["https://your-frontend.vercel.app","http://localhost:5173"]
```

Or if using Railway for frontend:
```bash
CORS_ORIGINS=["https://your-frontend.up.railway.app","http://localhost:5173"]
```

### 2. Update OAuth Redirect URI

If using Google OAuth:

1. **Google Cloud Console:**
   - Go to Credentials → Your OAuth Client
   - Update **Authorized redirect URIs**:
     ```
     https://your-frontend.vercel.app/oauth/callback
     ```

2. **Backend Environment Variable:**
   ```bash
   GOOGLE_REDIRECT_URI=https://your-frontend.vercel.app/oauth/callback
   ```

### 3. Test the Connection

Visit your frontend URL:
```
https://your-frontend.vercel.app
```

You should see the email generator interface. Check:
- [ ] Frontend loads without errors
- [ ] Can generate email (backend connection works)
- [ ] OAuth login works (if configured)
- [ ] Draft history loads

---

## Environment Variables Summary

### Frontend Environment Variables

| Variable | Value | Where to Set |
|----------|-------|--------------|
| `VITE_API_BASE_URL` | `https://your-backend.up.railway.app` | Vercel/Netlify/Railway Dashboard |

### Backend Environment Variables to Update

| Variable | Update to Include Frontend URL |
|----------|--------------------------------|
| `CORS_ORIGINS` | Add frontend URL to array |
| `GOOGLE_REDIRECT_URI` | Update to frontend callback URL |

---

## Build Locally (Optional)

Test the production build locally:

```bash
cd frontend

# Build
npm run build

# Preview production build
npm run preview
```

Visit `http://localhost:4173` to test the production build.

---

## Troubleshooting

### Issue: "API base URL missing"

**Cause:** `VITE_API_BASE_URL` not set in production environment.

**Fix:**
- Vercel: Dashboard → Settings → Environment Variables
- Netlify: Dashboard → Site Settings → Environment Variables  
- Railway: Service → Variables tab

### Issue: CORS Error

**Cause:** Backend CORS_ORIGINS doesn't include frontend URL.

**Fix:** Update backend `CORS_ORIGINS` environment variable in Railway.

### Issue: OAuth Callback Failed

**Cause:** Redirect URI mismatch.

**Fix:**
1. Update Google Cloud Console redirect URIs
2. Update backend `GOOGLE_REDIRECT_URI` variable
3. Ensure both match your frontend URL

### Issue: Build Fails

**Cause:** TypeScript errors or missing dependencies.

**Fix:**
```bash
cd frontend
npm install
npm run build
```

Check for errors and fix before deploying.

---

## Deployment Checklist

Before deploying:

- [ ] Backend is deployed and healthy on Railway
- [ ] Have backend URL (e.g., `https://your-app.up.railway.app`)
- [ ] Frontend builds locally without errors (`npm run build`)
- [ ] Chose deployment platform (Vercel/Netlify/Railway)
- [ ] Created account on chosen platform
- [ ] Ready to set `VITE_API_BASE_URL` environment variable

After deploying:

- [ ] Frontend loads without errors
- [ ] Set `VITE_API_BASE_URL` to backend URL
- [ ] Updated backend `CORS_ORIGINS`
- [ ] Tested email generation
- [ ] Updated OAuth redirect URIs (if using OAuth)
- [ ] Tested OAuth login flow (if using OAuth)

---

## Recommended Setup

**For Production:**
- ✅ **Backend:** Railway (Python/FastAPI)
- ✅ **Frontend:** Vercel (React/Vite)
- ✅ **Database:** Railway Redis + MongoDB Atlas (optional)

**Cost:**
- Railway Backend: ~$5/month
- Vercel Frontend: Free
- **Total: ~$5/month**

---

## Quick Commands

### Vercel Deployment
```bash
cd frontend
vercel                    # Preview deployment
vercel --prod            # Production deployment
vercel env add VITE_API_BASE_URL  # Add env var via CLI
```

### Netlify Deployment
```bash
cd frontend
netlify deploy           # Preview deployment
netlify deploy --prod    # Production deployment
netlify env:set VITE_API_BASE_URL https://your-backend.up.railway.app
```

### Railway Deployment
- Use dashboard (easier)
- Or push to GitHub and Railway auto-deploys

---

## Next Steps

1. ✅ Deploy backend to Railway (already done)
2. ⬜ Choose frontend platform (Vercel recommended)
3. ⬜ Deploy frontend
4. ⬜ Set `VITE_API_BASE_URL` environment variable
5. ⬜ Update backend `CORS_ORIGINS`
6. ⬜ Update OAuth redirect URIs
7. ⬜ Test end-to-end

**Ready to deploy? I recommend starting with Vercel - it's the easiest!**
