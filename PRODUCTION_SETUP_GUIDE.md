# Production Setup Guide

Complete guide for OAuth configuration, production infrastructure, and deployment.

---

## OAuth 2.0 Configuration

### Google OAuth Setup

#### 1. Google Cloud Console Configuration

1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (or select existing)
3. Add **Authorized redirect URIs**:
   ```
   https://email-generator-app-frontend.vercel.app
   http://localhost:5173 (for local development)
   ```
4. Save the credentials

#### 2. Railway Environment Variables

Set these **exact** values in Railway (Variables tab):

```bash
# Frontend URL
FRONTEND_URL=https://email-generator-app-frontend.vercel.app

# CORS Origins (comma-separated, NO brackets, NO extra quotes)
CORS_ORIGINS=https://email-generator-app-frontend.vercel.app,http://localhost:5173,http://localhost:3000

# Google OAuth Redirect URI (must match Google Console)
GOOGLE_REDIRECT_URI=https://email-generator-app-frontend.vercel.app

# Google OAuth Credentials (from Google Cloud Console)
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

#### 3. OAuth Flow (SPA Architecture)

1. User clicks "Sign in with Google" in frontend
2. Frontend calls `POST /auth/start` → gets Google authorization URL
3. User redirected to Google login
4. Google redirects back to: `https://email-generator-app-frontend.vercel.app?code=XXX&state=YYY`
5. Frontend reads `code` and `state` from URL
6. Frontend calls `POST /auth/exchange` with `{ provider, code, state }`
7. Backend exchanges code for token (server-side, secure)
8. Backend returns user info + session
9. Frontend saves session and shows logged-in state

### Verification Commands

After setup, verify with these PowerShell commands:

```powershell
# 1. Health check with CORS
$h = @{ Origin = "https://email-generator-app-frontend.vercel.app" }
(Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/health" -Headers $h).Headers["Access-Control-Allow-Origin"]

# 2. Auth providers
Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/auth/providers" -Headers $h

# 3. Start OAuth (check redirect_uri in response)
$r = Invoke-WebRequest -Uri "https://email-generator-app-production.up.railway.app/auth/start" -Method POST -ContentType "application/json" -Body '{"provider":"google"}' -Headers $h
($r.Content | ConvertFrom-Json).authorization_url
```

Expected results:
- CORS header: `Access-Control-Allow-Origin: https://email-generator-app-frontend.vercel.app`
- Authorization URL contains: `redirect_uri=https://email-generator-app-frontend.vercel.app`

### Common OAuth Mistakes

❌ **Wrong:** Setting `CORS_ORIGINS=["https://..."]` (JSON array)  
✅ **Right:** Setting `CORS_ORIGINS=https://email-generator-app-frontend.vercel.app,http://localhost:5173`

❌ **Wrong:** Google redirect URI = backend URL  
✅ **Right:** Google redirect URI = frontend URL (for SPA flow)

❌ **Wrong:** Adding extra quotes around Railway env values  
✅ **Right:** Paste raw value directly (Railway handles quoting)

---

## Production Infrastructure

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI API   │    │   Background    │
│                 │    │                 │    │   Workers       │
│ - OAuth login   │◄──►│ - Authentication│◄──►│ - Email queue   │
│ - Email forms   │    │ - Rate limiting │    │ - Cache warmup  │
│ - Chat interface│    │ - API endpoints │    │ - Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │    │   PostgreSQL    │    │   Gmail API     │
│                 │    │                 │    │                 │
│ - Sessions      │    │ - User data     │    │ - Send emails   │
│ - User profiles │    │ - Draft history │    │ - Manage drafts │
│ - Draft cache   │    │ - Preferences   │    │ - Read history  │
│ - Rate limits   │    │ - Analytics     │    │ - Thread context│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1. Caching Layer - Redis

**Why Redis?**
- High-performance in-memory caching
- Built-in data expiration (TTL)
- Support for complex data types
- Horizontal scaling capabilities
- Battle-tested in production

**Production setup:**
```bash
# Docker deployment
docker run -d --name redis-cache \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes

# Or managed service
# AWS ElastiCache, Google Cloud Memorystore, Azure Cache for Redis
```

**Environment variable:**
```bash
REDIS_URL=redis://localhost:6379
```

### 2. Database - PostgreSQL

**Current implementation:**
- Deployed on Railway
- Stores user profiles, draft history, preferences
- Connection pooling enabled

**Environment variable:**
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### 3. Email Integration - Gmail API

**Why Gmail?**
- Most widely used email service
- Comprehensive API with OAuth 2.0
- Support for drafts, sending, and reading
- Thread management capabilities
- Rich metadata and search

**Setup requirements:**
```json
// config/gmail_credentials.json
{
  "web": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost:8501/oauth/callback"]
  }
}
```

### 4. Future: ChromaDB (Vector Storage)

**Why ChromaDB?**
- Vector database optimized for AI applications
- Built-in embedding generation
- Semantic search capabilities
- Easy integration with LangChain
- Local and cloud deployment options

**Planned features:**
- Email context storage with vector embeddings
- Conversation history with semantic search
- User preference learning
- Similar email retrieval
- Context-aware suggestions

**Configuration:**
```bash
CHROMADB_PERSIST_DIR=/app/data/chromadb
DISABLE_CHROMADB=false
```

---

## Deployment Strategy

### Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if using)
docker run -d -p 6379:6379 redis:7-alpine

# Run backend
uvicorn src.api.main:app --reload --port 8000

# Run frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

---

## Production Deployment

### Backend Deployment - Railway

#### Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub repository connected
- Google Gemini API key
- OAuth credentials configured

#### Option A: One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Click the button above
2. Connect your GitHub account
3. Select this repository
4. Railway will auto-detect the Dockerfile

#### Option B: Manual Deploy via Dashboard

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `email-generator-app` repository
4. Railway will automatically:
   - Detect `Dockerfile`
   - Build the container
   - Deploy the service

#### Option C: Railway CLI

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

#### Add Redis Service

Your app needs Redis for caching and session management.

1. In Railway dashboard, click **"New"** → **"Database"** → **"Redis"**
2. Railway automatically sets `REDIS_URL` environment variable
3. No additional configuration needed

#### Configure Backend Environment Variables

In Railway dashboard → **Variables** tab, add:

**Required Variables:**
```bash
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Security (generate new for production)
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
ENABLE_GOOGLE_OAUTH=true

# Frontend URL (update after frontend deployment)
FRONTEND_URL=https://your-frontend-url.vercel.app
CORS_ORIGINS=https://your-frontend-url.vercel.app,http://localhost:5173
GOOGLE_REDIRECT_URI=https://your-frontend-url.vercel.app
```

**Optional Variables:**
```bash
# Disable features you don't need
ENABLE_GMAIL=false
ENABLE_CHROMADB=false
ENABLE_MCP=false

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

#### Test Backend Deployment

```bash
# Health Check
curl https://your-backend.railway.app/health

# Expected response
{
  "app_name": "AI Email Assistant"
}

# API Documentation
# Visit: https://your-backend.railway.app/docs

# Test Email Generation
curl -X POST https://your-backend.railway.app/email/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a professional follow-up email to John",
    "tone": "formal",
    "user_id": "test_user"
  }'
```

---

### Frontend Deployment

#### Option 1: Vercel (Recommended) ⭐

**Why Vercel?**
- ✅ Optimized for Vite/React
- ✅ Free tier with generous limits
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Automatic deployments from Git

**Deploy via Web Dashboard:**
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Set root directory to `frontend`
4. Framework will auto-detect as Vite
5. Add environment variable:
   ```
   VITE_API_BASE_URL = https://your-backend.up.railway.app
   ```
6. Click Deploy

**Deploy via CLI:**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Follow prompts:
# - Project name: email-generator-frontend
# - Framework: Vite (auto-detected)
# - Build command: npm run build
# - Output directory: dist

# Set environment variable
vercel env add VITE_API_BASE_URL

# Deploy to production
vercel --prod
```

#### Option 2: Netlify

**Deploy via Web Dashboard:**
1. Go to https://app.netlify.com/start
2. Connect GitHub repository
3. Set base directory to `frontend`
4. Build command: `npm run build`
5. Publish directory: `dist`
6. Add environment variable:
   ```
   VITE_API_BASE_URL = https://your-backend.up.railway.app
   ```

**Deploy via CLI:**
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
cd frontend
netlify deploy

# Set environment variable
netlify env:set VITE_API_BASE_URL https://your-backend.up.railway.app

# Deploy to production
netlify deploy --prod
```

#### Option 3: Railway (Keep Everything Together)

Deploy frontend as a separate Railway service in the same project.

1. **In Railway Dashboard:**
   - Go to your existing project
   - Click **"New Service"** → **"GitHub Repo"**
   - Select the same `email-generator-app` repository
   
2. **Configure Service:**
   - Click on the new service → **Settings**
   - Set **Root Directory** = `frontend`
   - Railway will auto-detect Vite

3. **Add Environment Variable:**
   - Go to **Variables** tab
   - Add:
     ```
     VITE_API_BASE_URL = https://your-backend.up.railway.app
     ```

4. **Deploy:**
   - Railway will automatically build and deploy

#### Post-Frontend Deployment

After deploying frontend, update backend configuration:

**Update Backend CORS in Railway:**
```bash
# Update these variables in Railway backend service
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
FRONTEND_URL=https://your-frontend.vercel.app
GOOGLE_REDIRECT_URI=https://your-frontend.vercel.app
```

**Update Google Cloud Console:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client
3. Add **Authorized redirect URIs**:
   ```
   https://your-frontend.vercel.app
   https://your-backend.railway.app/auth/callback/google
   ```
4. Save

**Test the Connection:**
Visit your frontend URL and verify:
- [ ] Frontend loads without errors
- [ ] Can generate email (backend connection works)
- [ ] OAuth login works (if configured)
- [ ] Draft history loads

---

### Docker Compose (Alternative)

For self-hosted deployments:

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - CORS_ORIGINS=http://localhost:5173,http://frontend:5173
    depends_on:
      - redis
      - postgres
      
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=emailgen
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  redis-data:
  postgres-data:
```

**Deploy:**
```bash
docker-compose up -d
```

---

### Recommended Production Setup

**For Production:**
- ✅ **Backend:** Railway (FastAPI + Redis)
- ✅ **Frontend:** Vercel (React/Vite)
- ✅ **Database:** Railway PostgreSQL

**Estimated Cost:**
- Railway Backend + Redis: ~$5-7/month (Hobby plan)
- Vercel Frontend: Free
- **Total: ~$5-7/month**

---

### Custom Domain (Optional)

#### Add Custom Domain to Railway

1. Railway Dashboard → **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Update your DNS records as shown
5. Railway will automatically provision SSL

#### Add Custom Domain to Vercel

1. Vercel Dashboard → **Settings** → **Domains**
2. Add your domain (e.g., `app.yourdomain.com`)
3. Update DNS records
4. Vercel auto-provisions SSL

#### Update Environment Variables

After adding custom domains, update:

**Backend (Railway):**
```bash
FRONTEND_URL=https://app.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com,http://localhost:5173
GOOGLE_REDIRECT_URI=https://app.yourdomain.com
```

**Frontend (Vercel):**
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## Configuration Management

### Environment Variables

**Required:**
```bash
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=postgresql://...
```

**Optional:**
```bash
REDIS_URL=redis://localhost:6379
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
DISABLE_OAUTH=false
DISABLE_GMAIL=false
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
CACHE_TTL_SECONDS=3600
```

### Configuration Files Structure
```
config/
├── oauth_config.json          # OAuth provider settings
├── gmail_credentials.json     # Gmail API credentials  
├── app_config.yaml           # Application settings
└── production_config.yaml    # Production overrides
```

---

## Monitoring and Logging

### Application Metrics to Track
- Email generation requests/minute
- Cache hit/miss ratios
- Authentication success/failure rates
- API response times
- Error rates by component
- Database connection pool usage
- Redis memory usage
- Gmail API quota usage

### View Logs

**Railway Backend Logs:**
```bash
# Via Dashboard
# Railway Dashboard → Deployments → View Logs

# Via CLI
railway logs
railway logs --follow  # Live tail
```

**Vercel Frontend Logs:**
```bash
# Via Dashboard
# Vercel Dashboard → Deployments → Select deployment → View Logs

# Via CLI
vercel logs
```

### Railway Metrics

Railway provides built-in monitoring:
- **CPU Usage**
- **Memory Usage**
- **Network Traffic**
- **Request Count**

Access: Railway Dashboard → **Metrics** tab

### Logging Strategy
```python
import logging

# Structured logging for production
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Key events to log:
# - User authentication events
# - Email generation requests
# - Cache operations
# - External API calls
# - Error conditions
```

### External Monitoring (Recommended)

Set up external monitoring:
- **Uptime:** UptimeRobot, Pingdom
- **Errors:** Sentry
- **Analytics:** PostHog, Mixpanel

---

## Scaling and Performance

### Auto-Scaling

**Railway Auto-Scaling:**
Railway auto-scales based on:
- CPU usage
- Memory usage
- Request volume

**Manual Scaling:**

Update via environment variables:
```bash
WEB_CONCURRENCY=4  # Number of uvicorn workers
```

Or use Railway's replica settings in dashboard.

### Performance Optimization

**Backend:**
- Enable Redis caching
- Implement rate limiting
- Monitor LLM token usage
- Use connection pooling for database

**Frontend:**
- Use CDN (Vercel provides this automatically)
- Enable compression
- Lazy load components
- Optimize bundle size

---

## Deployment Troubleshooting

### Backend Build Fails

```bash
# Check build logs
railway logs --deployment

# Common fixes:
1. Verify Dockerfile syntax
2. Check requirements.txt is complete
3. Ensure Python 3.11 compatibility
```

### Backend Runtime Errors

```bash
# Check live logs
railway logs --follow

# Common issues:
1. Missing environment variables
2. Redis connection (ensure Redis service is added)
3. CORS misconfiguration (check CORS_ORIGINS)
4. Database connection string format
```

### Frontend Build Fails

```bash
# Check Vercel build logs in dashboard

# Common issues:
1. TypeScript errors
2. Missing dependencies (run `npm install` locally)
3. Environment variable not set
4. Build command incorrect
```

### Frontend Runtime Issues

**Symptom:** "API base URL missing"
- **Fix:** Set `VITE_API_BASE_URL` in Vercel/Netlify dashboard

**Symptom:** CORS Error
- **Fix:** Update backend `CORS_ORIGINS` to include frontend URL

**Symptom:** OAuth Callback Failed
- **Fix:** 
  1. Update Google Cloud Console redirect URIs
  2. Update backend `GOOGLE_REDIRECT_URI`
  3. Ensure both match frontend URL

### Connection Issues

**Connection Refused:**
- Ensure backend listens on `0.0.0.0` not `localhost`
- Check `PORT` environment variable is used
- Verify health check endpoint exists

**OAuth Not Working:**
1. Check redirect URIs in Google Console
2. Verify `GOOGLE_REDIRECT_URI` matches frontend URL
3. Ensure `ENABLE_GOOGLE_OAUTH=true`
4. Clear browser cache and test in incognito

---

## CI/CD and Deployment Automation

### Railway Auto-Deployment

Railway automatically deploys when you push to GitHub.

**Configure:**
1. Railway Dashboard → **Settings** → **Source**
2. Set branch (e.g., `main`, `production`)

**Disable auto-deploy:**
1. Railway Dashboard → **Settings**
2. Uncheck "Deploy on push"

### Vercel Auto-Deployment

Vercel automatically deploys:
- **Production:** Pushes to `main` branch
- **Preview:** Pull requests and other branches

**Configure:**
1. Vercel Dashboard → **Settings** → **Git**
2. Set production branch
3. Configure branch deployment settings

### Rollback

**Railway Rollback:**
1. Railway Dashboard → **Deployments**
2. Find last working deployment
3. Click **"Redeploy"**

Or via CLI:
```bash
railway rollback
```

**Vercel Rollback:**
1. Vercel Dashboard → **Deployments**
2. Find previous deployment
3. Click **"Promote to Production"**

---

## Backup and Data Management

### Database Backups

**Railway PostgreSQL:**
- Railway provides automated backups
- Access via dashboard: Database → Backups tab

**Manual Backup:**
```bash
# Export database
railway run pg_dump > backup.sql

# Restore database
railway run psql < backup.sql
```

### User Data Export

Periodically export user data:
- User profiles
- Draft history
- Preferences

Store in external storage (S3, Google Cloud Storage).

---

## Environment-Specific Settings

Railway automatically sets these:

```bash
PORT                    # Application port (auto-assigned)
RAILWAY_ENVIRONMENT     # "production"
RAILWAY_PROJECT_NAME    # Your project name
REDIS_URL              # When Redis service added
DATABASE_URL           # When PostgreSQL service added
```

Use in code:
```python
import os

is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production"
port = int(os.getenv("PORT", 8000))
```

---

## Security Best Practices

### Security Checklist

**Data Protection:**
- ✅ HTTPS only in production (Railway/Vercel provide this automatically)
- ✅ OAuth tokens encrypted at rest
- ✅ Proper CORS configuration
- ✅ Secure cookie settings
- ✅ Environment variables for secrets (never commit to Git)
- ✅ `.env` files in `.gitignore`

**Access Control:**
- ✅ User data segregation
- ✅ Rate limiting per user
- ✅ JWT token expiration
- ✅ Audit logging for sensitive operations

**Before Production Deployment:**
- [ ] `DEBUG=false` in production
- [ ] Generate new `JWT_SECRET_KEY` (never use default)
- [ ] Restrict CORS to your domains only
- [ ] Update OAuth redirect URIs to production URLs
- [ ] Review `.dockerignore` (no secrets in image)
- [ ] Environment variables in Railway/Vercel (not in code)
- [ ] Enable rate limiting (`ENABLE_RATE_LIMITER=true`)
- [ ] Test OAuth flow end-to-end
- [ ] Verify API endpoints require authentication

### Generate Secure Secrets

```bash
# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API keys
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Troubleshooting

### CORS Issues
1. **Symptom:** CORS errors on `/auth/exchange` or API calls
2. **Fix:** Verify `CORS_ORIGINS` in Railway matches frontend URL exactly
3. **Verify:** Check Railway logs for startup message showing resolved CORS origins
4. **Test:**
   ```powershell
   $h = @{ Origin = "https://your-frontend.vercel.app" }
   (Invoke-WebRequest -Uri "https://your-backend.railway.app/health" -Headers $h).Headers["Access-Control-Allow-Origin"]
   ```

### OAuth Failures
1. **Symptom:** 500 Internal Server Error during callback
2. **Fix:** Ensure `GOOGLE_REDIRECT_URI` matches Google Cloud Console configuration
3. **Verify:** Test `/auth/start` endpoint and check `redirect_uri` in response
4. **Check:** Frontend URL matches exactly (no trailing slash differences)

### Database Connection Issues
1. **Symptom:** Connection timeout or refused
2. **Fix:** Verify `DATABASE_URL` is correctly formatted in Railway
3. **Verify:** Check Railway PostgreSQL service is running
4. **Format:** `postgresql://user:password@host:port/database`

### API Quota Errors
1. **Symptom:** OpenAI/Gemini API quota exceeded
2. **Fix:** Check API billing and quota limits
3. **Verify:** Monitor API usage in provider dashboard
4. **Optimize:** Enable caching to reduce API calls

### Frontend Not Loading
1. **Check:** Vercel deployment logs for build errors
2. **Verify:** `VITE_API_BASE_URL` is set correctly
3. **Test:** Visit `https://your-frontend.vercel.app` in incognito
4. **Clear:** Browser cache and hard refresh (Ctrl+Shift+R)

### Email Generation Failing
1. **Check:** Backend logs in Railway
2. **Verify:** `GEMINI_API_KEY` is set and valid
3. **Test:** API endpoint directly with curl
4. **Monitor:** LLM token usage and quota

---

## Cost Optimization

### Caching Strategy
- Cache similar prompts to reduce LLM API costs
- Implement prompt deduplication
- Use cheaper models for simple tasks
- Set appropriate TTL for cached responses

### Resource Management
- Monitor actual usage patterns
- Use auto-scaling (Railway Hobby plan scales to 0)
- Implement graceful degradation
- Set connection pool limits appropriately

---

## Quick Start Deployment Guide

### Step-by-Step Deployment

**1. Deploy Backend to Railway** ⏱️ 5 minutes
- [ ] Sign up at https://railway.app
- [ ] Click "Deploy from GitHub repo"
- [ ] Select `email-generator-app` repository
- [ ] Add Redis service (New → Database → Redis)
- [ ] Set environment variables (see Backend Environment Variables section)
- [ ] Wait for deployment to complete
- [ ] Test: `curl https://your-backend.railway.app/health`

**2. Deploy Frontend to Vercel** ⏱️ 3 minutes
- [ ] Sign up at https://vercel.com
- [ ] Click "Import Project" → GitHub
- [ ] Select repository, set root directory to `frontend`
- [ ] Add environment variable: `VITE_API_BASE_URL=https://your-backend.railway.app`
- [ ] Deploy
- [ ] Test: Visit `https://your-frontend.vercel.app`

**3. Update Backend Configuration** ⏱️ 2 minutes
- [ ] In Railway, update backend environment variables:
  - `CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173`
  - `FRONTEND_URL=https://your-frontend.vercel.app`
  - `GOOGLE_REDIRECT_URI=https://your-frontend.vercel.app`
- [ ] Wait for Railway to redeploy

**4. Configure Google OAuth** ⏱️ 3 minutes
- [ ] Go to https://console.cloud.google.com/apis/credentials
- [ ] Edit OAuth 2.0 Client
- [ ] Add redirect URI: `https://your-frontend.vercel.app`
- [ ] Save

**5. Test Everything** ⏱️ 5 minutes
- [ ] Visit frontend URL
- [ ] Try OAuth login
- [ ] Generate a test email
- [ ] Check draft history
- [ ] Verify in Railway/Vercel logs

**Total Time: ~20 minutes** 🎉

---

## Complete Deployment Checklist

### Pre-Deployment
- [ ] Repository pushed to GitHub
- [ ] Google OAuth credentials created
- [ ] Gemini API key obtained
- [ ] Railway account created
- [ ] Vercel account created

### Backend Deployment (Railway)
- [ ] Backend service deployed to Railway
- [ ] Redis service added
- [ ] All required environment variables set
- [ ] Health check endpoint responds
- [ ] API documentation accessible (if DEBUG=true)

### Frontend Deployment (Vercel)
- [ ] Frontend deployed to Vercel
- [ ] `VITE_API_BASE_URL` environment variable set
- [ ] Frontend loads without errors
- [ ] Can communicate with backend API

### OAuth Configuration
- [ ] Google Cloud Console redirect URIs updated
- [ ] Backend `GOOGLE_REDIRECT_URI` matches frontend URL
- [ ] Backend `CORS_ORIGINS` includes frontend URL
- [ ] OAuth login flow tested end-to-end

### Security & Monitoring
- [ ] `DEBUG=false` in production
- [ ] New `JWT_SECRET_KEY` generated
- [ ] CORS restricted to production domains
- [ ] Rate limiting enabled
- [ ] Logs accessible in Railway/Vercel
- [ ] Error monitoring set up (optional: Sentry)

### Testing
- [ ] Health check works
- [ ] Email generation works
- [ ] OAuth login works
- [ ] Draft history loads
- [ ] All API endpoints functional
- [ ] Frontend-backend communication verified

---

## Cost Optimization

### Caching Strategy
- Cache similar prompts to reduce LLM API costs
- Implement prompt deduplication
- Use cheaper models for simple tasks
- Set appropriate TTL for cached responses
- Monitor cache hit rates in Redis

### Resource Management
- Monitor actual usage patterns
- Use auto-scaling (Railway Hobby plan scales to 0 when idle)
- Implement graceful degradation
- Set connection pool limits appropriately
- Review LLM token usage regularly

### Cost Breakdown (Monthly Estimates)

**Infrastructure:**
- Railway Backend: $3-5/month
- Railway Redis: $2/month
- Vercel Frontend: Free
- **Subtotal: $5-7/month**

**API Usage (Variable):**
- Gemini API: Pay per use (~$0.10-$5/month for light usage)
- Gmail API: Free (with quotas)
- **Subtotal: $0.10-$5/month**

**Total Estimated Cost: $5-$12/month**

*Costs can be lower with Railway's Hobby plan if your app scales to zero during idle periods.*

---

_Last Updated: November 15, 2025_
