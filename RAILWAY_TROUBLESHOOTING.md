# Railway Deployment Troubleshooting

## Health Check Failures

### Issue: "1/1 replicas never became healthy"

This error occurs when Railway's health check endpoint doesn't respond as expected.

### Common Causes & Fixes

#### 1. Missing Required Environment Variables

**Symptom:** App crashes on startup due to missing configuration.

**Fix:**
```bash
# Required environment variables in Railway Dashboard:
GEMINI_API_KEY=<your_key>
JWT_SECRET_KEY=<generate_secure_key>
```

**Optional but recommended:**
```bash
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-app.up.railway.app"]
```

#### 2. Health Check Timeout

**Symptom:** Health check takes too long to respond.

**Fix:** Increased timeout in `railway.json`:
```json
{
  "deploy": {
    "healthcheckTimeout": 300
  }
}
```

#### 3. Port Configuration Issues

**Symptom:** App listens on wrong port.

**Fix:** Railway automatically sets `$PORT` environment variable. Our config uses it:
```json
{
  "deploy": {
    "startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

#### 4. Dependencies Not Installing

**Symptom:** Import errors in logs.

**Fix:** Check Dockerfile installs all dependencies:
```dockerfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
```

#### 5. Worker Configuration Issues

**Issue:** Multiple workers can cause issues with Railway's resource limits.

**Fix:** Use single worker for initial deployment:
```json
{
  "deploy": {
    "startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

Scale up workers after successful deployment if needed.

---

## Debugging Steps

### Step 1: Check Deploy Logs

In Railway Dashboard:
1. Go to **Deployments** tab
2. Click on the failed deployment
3. View **Deploy Logs** tab
4. Look for error messages

Common errors:
```
ModuleNotFoundError: No module named 'X'
  → Missing dependency in requirements.txt

KeyError: 'GEMINI_API_KEY'
  → Missing environment variable

Error binding to port
  → Port configuration issue
```

### Step 2: Verify Environment Variables

Railway Dashboard → **Variables** tab:
- ✅ `GEMINI_API_KEY` is set
- ✅ `JWT_SECRET_KEY` is set
- ✅ No quotes around values
- ✅ No trailing spaces

### Step 3: Test Locally with Docker

Build and run the exact same container:

```bash
# Build Docker image
docker build -t email-generator .

# Run with environment variables
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=<your_key> \
  -e JWT_SECRET_KEY=<your_secret> \
  -e PORT=8000 \
  email-generator

# Test health endpoint
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "app_name": "AI Email Generator",
  "version": "1.0.0"
}
```

### Step 4: Verify Health Check Endpoint

Test the health check locally:

```bash
# Start local server
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# In another terminal, test health check
curl http://localhost:8000/health

# Should return:
# {"status":"ok","app_name":"AI Email Generator","version":"1.0.0"}
```

### Step 5: Check Pydantic Schema

The health check response model requires:
```python
class HealthCheckResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
```

Ensure the endpoint returns all required fields:
```python
@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="ok",
        app_name=settings.app_name,
        version="1.0.0"
    )
```

---

## Recent Fixes Applied

### Fix 1: Health Check Response Model ✅
**Issue:** Missing `version` field in health check response.

**Before:**
```python
return HealthCheckResponse(app_name=settings.app_name)
```

**After:**
```python
return HealthCheckResponse(
    status="ok",
    app_name=settings.app_name,
    version="1.0.0"
)
```

### Fix 2: Removed Multiple Workers ✅
**Issue:** 4 workers can exceed Railway's free tier memory limits.

**Before:**
```json
"startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 4"
```

**After:**
```json
"startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
```

### Fix 3: Fixed Python Module Path ✅
**Issue:** Railway couldn't find `src.api.main` module.

**Root Cause:** Python wasn't looking in the correct directory for modules.

**Solutions Applied:**

1. **Added PYTHONPATH to Dockerfile:**
```dockerfile
ENV PYTHONPATH=/app
```

2. **Updated start command to use `python -m`:**
```json
"startCommand": "cd /app && python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
```

3. **Updated Dockerfile CMD:**
```dockerfile
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Using `python -m uvicorn` instead of just `uvicorn` ensures Python uses the correct module resolution.

### Fix 4: Increased Health Check Timeout ✅
**Issue:** 100s might be too short for cold start.

**Before:**
```json
"healthcheckTimeout": 100
```

**After:**
```json
"healthcheckTimeout": 300
```

### Fix 4: Enhanced Dockerfile ✅
**Improvements:**
- Set `PYTHONUNBUFFERED=1` for real-time logs
- Upgrade pip before installing dependencies
- Added `--log-level info` for better debugging
- Added Docker health check

---

## Deployment Checklist

Before redeploying, verify:

- [ ] All environment variables set in Railway Dashboard
- [ ] `GEMINI_API_KEY` is valid (test locally first)
- [ ] `JWT_SECRET_KEY` is a strong random string
- [ ] Health check endpoint works locally: `curl http://localhost:8000/health`
- [ ] Docker image builds successfully: `docker build -t test .`
- [ ] No sensitive data in code (all in env vars)
- [ ] `requirements.txt` has all dependencies with versions
- [ ] `.dockerignore` excludes unnecessary files

---

## Testing Health Check Locally

### Method 1: Direct Python

```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Start server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# In another terminal
curl http://localhost:8000/health
```

### Method 2: With Docker

```bash
# Build image
docker build -t email-gen-test .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=$env:GEMINI_API_KEY \
  -e JWT_SECRET_KEY="test-secret-key-12345" \
  -e PORT=8000 \
  email-gen-test

# Test
curl http://localhost:8000/health
```

### Method 3: Using Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs in real-time
railway logs --follow

# Open shell in deployment
railway shell
```

---

## Minimal Environment Variables for Testing

For initial deployment test, you only need:

```bash
GEMINI_API_KEY=<your_actual_key>
JWT_SECRET_KEY=railway-test-secret-key-$(openssl rand -hex 32)
DEBUG=true
```

Add OAuth and database configs after basic deployment works.

---

## Next Steps After Health Check Passes

1. ✅ Health check successful
2. ⬜ Test root endpoint: `https://your-app.up.railway.app/`
3. ⬜ Test API docs: `https://your-app.up.railway.app/docs`
4. ⬜ Test email generation endpoint
5. ⬜ Add Redis service
6. ⬜ Configure OAuth redirect URIs
7. ⬜ Deploy frontend
8. ⬜ Connect frontend to backend

---

## Common Railway Error Messages

### "Application failed to respond"
**Cause:** App not listening on correct port or crashed.
**Fix:** Check logs for startup errors, verify `PORT` env var usage.

### "Build failed"
**Cause:** Dockerfile syntax error or missing dependencies.
**Fix:** Test Docker build locally first.

### "Out of memory"
**Cause:** Too many workers or memory-intensive operations.
**Fix:** Reduce workers, upgrade Railway plan.

### "Health check timeout"
**Cause:** App takes too long to start or respond.
**Fix:** Increase timeout, optimize startup time.

---

## Contact & Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/docker/
- **This Project's Deployment Guide:** See `RAILWAY_DEPLOYMENT.md`

---

**After applying fixes, redeploy:**

```bash
git add .
git commit -m "Fix Railway health check issues"
git push origin dev_fastapi
```

Railway will automatically detect the push and redeploy!
