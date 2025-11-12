# Railway Deployment - Quick Reference

## ✅ Pre-Deployment Checklist

Your repository is now **Railway-ready** with the following configurations:

### Files Created

- ✅ `Dockerfile` - Container configuration
- ✅ `railway.json` - Railway deployment settings  
- ✅ `.dockerignore` - Excludes unnecessary files from Docker image
- ✅ `.env.railway` - Production environment template
- ✅ `start.py` - Railway-optimized startup script
- ✅ `check_railway.py` - Pre-deployment validation tool
- ✅ `RAILWAY_DEPLOYMENT.md` - Complete deployment guide
- ✅ `frontend/railway.toml` - Frontend deployment config
- ✅ `.github/workflows/railway-deploy.yml` - CI/CD pipeline

### Code Updates

- ✅ `src/api/main.py` - Added Railway environment detection
- ✅ `requirements.txt` - Optimized for production deployment
- ✅ `README.md` - Added deployment documentation

---

## 🚀 Deploy Now (3 Steps)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Railway deployment configuration"
git push origin dev_fastapi
```

### Step 2: Create Railway Project

**Option A: Web Dashboard**
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `email-generator-app`
4. Railway auto-detects Dockerfile and deploys!

**Option B: CLI**
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Step 3: Configure Environment Variables

In Railway Dashboard → **Variables**, add:

**Required:**
```bash
GEMINI_API_KEY=<your_key>
JWT_SECRET_KEY=<generate_new_secret>
```

**OAuth (if using):**
```bash
ENABLE_GOOGLE_OAUTH=true
GOOGLE_CLIENT_ID=<your_client_id>
GOOGLE_CLIENT_SECRET=<your_secret>
```

**Update after deployment:**
```bash
GOOGLE_REDIRECT_URI=https://your-app.up.railway.app/oauth/callback
CORS_ORIGINS=["https://your-app.up.railway.app"]
```

---

## 📦 Add Services

### Redis (Recommended)

1. Railway Dashboard → **New** → **Database** → **Redis**
2. Automatically sets `REDIS_URL` environment variable
3. No additional config needed!

### MongoDB (Optional)

**Option 1: Railway MongoDB**
1. Dashboard → **New** → **Database** → **MongoDB**
2. Auto-sets connection string

**Option 2: MongoDB Atlas**
1. Use existing connection string from `.env`
2. Set in Railway: `MONGODB_CONNECTION_STRING`

---

## 🎯 Deployment Status

Run this command to verify readiness:

```bash
.\.venv\Scripts\python.exe check_railway.py
```

**Current Status:** ✅ ALL CHECKS PASSED

---

## 🔧 Environment Configuration

### Current `.env` (Local Development)
- ✅ Gemini API Key configured
- ✅ JWT Secret set
- ✅ Google OAuth configured
- ✅ Redis configured (localhost)
- ✅ MongoDB Atlas configured

### Production `.env.railway` Template
Copy values from `.env.railway` to Railway dashboard, updating:
- Redirect URIs with Railway domain
- CORS origins with Railway domain
- Set `DEBUG=false`
- Set `LOG_LEVEL=WARNING`

---

## 🌐 Frontend Deployment

### Option 1: Railway (Same Project)

1. Railway → **New Service** → Connect same repo
2. Set **Root Directory** = `frontend`
3. Add env var: `VITE_API_BASE_URL=https://your-backend.up.railway.app`
4. Railway auto-detects Vite and builds

### Option 2: Vercel/Netlify

```bash
cd frontend
npm run build
vercel --prod  # or netlify deploy --prod
```

Update backend:
```bash
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

---

## 📊 Cost Estimate

**Railway Hobby Plan ($5/month):**
- Backend service: ~$3/month
- Redis: ~$2/month  
- **Total: ~$5-7/month**

**Railway Pro Plan ($20/month):**
- Better performance
- More resources
- Recommended for production

---

## 🔍 Monitoring

### View Logs
```bash
railway logs
railway logs --follow  # Real-time
```

### Health Check
```bash
curl https://your-app.up.railway.app/health
```

### API Docs
Visit: `https://your-app.up.railway.app/docs`
(Only available if `DEBUG=true`)

---

## 🐛 Troubleshooting

### Build Fails
```bash
railway logs --deployment
```

Common fixes:
- Check `Dockerfile` syntax
- Verify all dependencies in `requirements.txt`
- Ensure Python 3.11+ compatibility

### Runtime Errors
```bash
railway logs --follow
```

Common issues:
- Missing environment variables
- Redis not connected (add Redis service)
- CORS misconfiguration

### OAuth Not Working
1. Update redirect URI in Google Cloud Console
2. Match `GOOGLE_REDIRECT_URI` in Railway
3. Ensure `ENABLE_GOOGLE_OAUTH=true`

---

## 📚 Documentation

- **Deployment Guide:** [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway

---

## 🎉 Next Steps After Deployment

1. ✅ Deploy backend to Railway
2. ✅ Add Redis service  
3. ✅ Configure environment variables
4. ⬜ Deploy frontend
5. ⬜ Update OAuth redirect URIs
6. ⬜ Test all endpoints
7. ⬜ Set up custom domain (optional)
8. ⬜ Configure monitoring (Sentry, etc.)

---

## 🔐 Security Checklist

Before going live:

- [ ] `DEBUG=false` in production
- [ ] Generate new `JWT_SECRET_KEY` for production
- [ ] Restrict CORS to your domain only
- [ ] Update OAuth redirect URIs
- [ ] Review `.dockerignore` (no secrets in image)
- [ ] All secrets in Railway environment (not in code)
- [ ] Rate limiting enabled
- [ ] HTTPS enabled (automatic in Railway)

---

**Your app is Railway-ready! 🚀**

Run deployment check anytime:
```bash
.\.venv\Scripts\python.exe check_railway.py
```
