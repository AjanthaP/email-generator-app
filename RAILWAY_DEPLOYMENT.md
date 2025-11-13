# Railway Deployment Guide

## Quick Start

### 1. Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub repository connected
- Google Gemini API key
- OAuth credentials configured (for Google login)

### 2. Deploy to Railway

**Option A: One-Click Deploy**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Click the button above
2. Connect your GitHub account
3. Select this repository
4. Railway will auto-detect the Dockerfile

**Option B: Manual Deploy via Dashboard**

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `email-generator-app` repository
4. Railway will automatically:
   - Detect `Dockerfile`
   - Build the container
   - Deploy the service

**Option C: Railway CLI**

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to your project
railway link

# Deploy
railway up
```

---

## 3. Add Redis Service

Your app needs Redis for caching and session management.

1. In Railway dashboard, click **"New"** → **"Database"** → **"Redis"**
2. Railway automatically sets `REDIS_URL` environment variable
3. No additional configuration needed

---

## 4. Configure Environment Variables

In Railway dashboard → **Variables** tab, add the following:

### Required Variables

```bash
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Security (generate new for production)
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
ENABLE_GOOGLE_OAUTH=true
```

### Update After First Deploy

After Railway assigns your URL (e.g., `https://your-app.up.railway.app`), update:

```bash
# OAuth Redirect
GOOGLE_REDIRECT_URI=https://your-frontend-url.railway.app/oauth/callback

# CORS
CORS_ORIGINS=["https://your-frontend-url.railway.app","http://localhost:5173"]
ALLOWED_HOSTS=["your-app.up.railway.app"]
```

### Optional Variables

```bash
# MongoDB (if you want to use it instead of local files)
ENABLE_MONGODB=true
MONGODB_CONNECTION_STRING=your_mongodb_atlas_connection_string

# Disable features you don't need
ENABLE_GMAIL=false
ENABLE_CHROMADB=false
ENABLE_MCP=false
```

---

## 5. Deploy Frontend (React)

### Option A: Deploy Frontend to Railway

1. In Railway project, click **"New Service"**
2. Select your repository again (or fork frontend to separate repo)
3. Set **Root Directory** to `frontend`
4. Railway will auto-detect Vite
5. Add environment variable:
   ```bash
   VITE_API_BASE_URL=https://your-backend.up.railway.app
   ```

### Option B: Deploy Frontend to Vercel/Netlify

```bash
# Build frontend locally
cd frontend
npm install
npm run build

# Deploy dist/ to Vercel
vercel --prod

# Or Netlify
netlify deploy --prod --dir=dist
```

Update backend CORS:
```bash
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

---

## 6. Update OAuth Settings

In **Google Cloud Console** (https://console.cloud.google.com):

1. Go to **APIs & Services** → **Credentials**
2. Edit your OAuth 2.0 Client
3. Add **Authorized redirect URIs**:
   ```
  https://your-frontend.railway.app/oauth/callback
  https://your-backend.railway.app/api/auth/callback/google
   ```
4. Save

---

## 7. Test Deployment

### Health Check

```bash
curl https://your-backend.railway.app/health
```

Expected response:
```json
{
  "app_name": "AI Email Assistant"
}
```

### API Documentation

Visit: `https://your-backend.railway.app/docs`

(Only available if `DEBUG=true`)

### Generate Email Test

```bash
curl -X POST https://your-backend.railway.app/api/v1/email/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a professional follow-up email to John",
    "tone": "formal",
    "user_id": "test_user"
  }'
```

---

## 8. Custom Domain (Optional)

### Add Custom Domain to Railway

1. Railway Dashboard → **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Update your DNS records as shown
5. Railway will automatically provision SSL

### Update Environment Variables

```bash
GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/callback
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com"]
```

---

## 9. Monitoring & Logs

### View Logs

**Via Dashboard:**
- Railway Dashboard → **Deployments** → **View Logs**

**Via CLI:**
```bash
railway logs
railway logs --follow  # Live tail
```

### Metrics

Railway provides built-in monitoring:
- **CPU Usage**
- **Memory Usage**
- **Network Traffic**
- **Request Count**

Access: Railway Dashboard → **Metrics** tab

---

## 10. Environment-Specific Settings

Railway automatically sets these:

- `PORT` - Application port (don't override)
- `RAILWAY_ENVIRONMENT` - "production"
- `RAILWAY_PROJECT_NAME` - Your project name
- `REDIS_URL` - When Redis service added

Use in code:
```python
import os
is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production"
```

---

## Project Architecture on Railway

```
┌─────────────────────────────────────────┐
│          Railway Project                 │
├─────────────────────────────────────────┤
│                                          │
│  ┌──────────────┐    ┌──────────────┐  │
│  │   Backend    │───▶│    Redis     │  │
│  │  (FastAPI)   │    │   (Plugin)   │  │
│  │              │    │              │  │
│  │ Port: $PORT  │    │ Auto-config  │  │
│  └──────────────┘    └──────────────┘  │
│         │                                │
│         ▼                                │
│  ┌──────────────┐                       │
│  │   Frontend   │                       │
│  │   (React)    │                       │
│  │   Optional   │                       │
│  └──────────────┘                       │
│                                          │
└─────────────────────────────────────────┘
         │
         ▼
   Internet Users
```

---

## Cost Estimation

### Railway Pricing

- **Hobby Plan**: $5/month
  - 500 execution hours
  - $0.000231/GB-hour for RAM
  - Perfect for small projects

- **Pro Plan**: $20/month
  - More resources
  - Better for production

### Your App Resource Usage

Estimated monthly cost (Hobby plan):
- **Backend Service**: ~$3-5/month
- **Redis Plugin**: ~$2/month
- **Total**: ~$5-7/month

---

## Troubleshooting

### Build Fails

```bash
# Check build logs
railway logs --deployment

# Common fixes:
1. Verify Dockerfile syntax
2. Check requirements.txt is complete
3. Ensure Python 3.11 compatibility
```

### Runtime Errors

```bash
# Check live logs
railway logs --follow

# Common issues:
1. Missing environment variables
2. Redis connection (ensure Redis service is added)
3. CORS misconfiguration (check CORS_ORIGINS)
```

### Connection Refused

- Ensure app listens on `0.0.0.0` not `localhost`
- Check `PORT` environment variable is used
- Verify health check endpoint exists

### OAuth Not Working

1. Check redirect URIs in Google Console
2. Verify `GOOGLE_REDIRECT_URI` matches frontend URL
3. Ensure `ENABLE_GOOGLE_OAUTH=true`

---

## Security Checklist

Before going to production:

- [ ] `DEBUG=false` in production
- [ ] Generate new `JWT_SECRET_KEY`
- [ ] Restrict CORS to your domains only
- [ ] Update OAuth redirect URIs
- [ ] Review `.dockerignore` (no secrets in image)
- [ ] Environment variables in Railway (not in code)
- [ ] HTTPS enabled (Railway does this automatically)
- [ ] Rate limiting enabled (`ENABLE_RATE_LIMITER=true`)

---

## Scaling

### Auto-Scaling

Railway auto-scales based on:
- CPU usage
- Memory usage
- Request volume

### Manual Scaling

Update `railway.json`:
```json
{
  "deploy": {
    "numReplicas": 2,
    "startCommand": "uvicorn src.api.main:app --workers 4"
  }
}
```

Or set via environment:
```bash
WEB_CONCURRENCY=4  # Number of uvicorn workers
```

---

## Rollback

If deployment fails:

1. Railway Dashboard → **Deployments**
2. Find last working deployment
3. Click **"Redeploy"**

Or via CLI:
```bash
railway rollback
```

---

## CI/CD Integration

Railway automatically deploys when you push to GitHub.

**Disable auto-deploy:**
1. Railway Dashboard → **Settings**
2. Uncheck "Deploy on push"

**Deploy specific branch:**
1. Settings → **Source**
2. Set branch (e.g., `main`, `production`)

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Add Redis service
3. ✅ Configure environment variables
4. ✅ Deploy frontend
5. ✅ Update OAuth settings
6. ✅ Test endpoints
7. 🚀 Go live!

**Need help?**
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

---

## Production Best Practices

### Monitoring

Set up external monitoring:
- **Uptime**: UptimeRobot, Pingdom
- **Errors**: Sentry
- **Analytics**: PostHog, Mixpanel

### Backups

Railway doesn't backup your data automatically:
- Export user data periodically
- Use MongoDB Atlas with automated backups
- Store drafts in external storage (S3, Cloudinary)

### Performance

Optimize for production:
- Enable Redis caching
- Use CDN for frontend (Cloudflare)
- Implement rate limiting
- Monitor LLM token usage

---

**Your app is now Railway-ready! 🚀**
