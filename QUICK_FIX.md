# Quick Fix: Stop Hitting Quota Limits

## The Problem
**You see "1 Request" but hit quota limits because each email generation makes 6 separate Gemini API calls** (one per agent: parser → intent → draft → tone → personalization → review).

Gemini's free tier experimental model (`gemini-2.0-flash-exp`) allows only **2-5 requests/minute** → your 6 rapid calls exceed this immediately.

---

## Instant Fix (Choose One)

### Option A: Switch to Stable Model (Recommended)
Edit `.env`:
```env
GEMINI_MODEL=gemini-1.5-flash
```

**Why:** Higher free tier limits (15 RPM vs 2 RPM), production-ready, same cost.

### Option B: Enable Rate Limiting
Add to `.env`:
```env
ENABLE_RATE_LIMITER=true
REQUESTS_PER_MINUTE=10
```

**Why:** Spreads your 6 calls over 10-15 seconds to stay under quota.  
**Trade-off:** Slower email generation.

### Option C: Upgrade to Paid Tier
Go to [Google AI Studio](https://aistudio.google.com/apikey) → Enable billing.

**Why:** 300 RPM, costs ~$0.01/day for 100 emails.

---

## Verify the Fix

1. Restart Streamlit (Ctrl+C, then re-run)
2. Generate an email
3. Check sidebar **Session Metrics**:
   - **LLM Calls** should show 5-6 (the real count)
   - **Successful** should match LLM Calls (no errors)
   - **Output Tokens** should be > 0

---

## New Metrics Panel

After the latest update, the sidebar now shows:
- **LLM Calls** — actual API calls made (not user requests)
- **Successful** — calls that worked
- **Errors** — quota/network failures
- **Input/Output Tokens** — token usage breakdown
- **Avg Latency** — response time per call

This helps you see exactly what's happening behind the scenes.

---

## Still Getting Errors?

1. Check `DEBUG=True` is in `.env`
2. Restart Streamlit
3. Generate one email
4. Click **"Flush Metrics to Disk"** in sidebar
5. Share the JSON file from `data/metrics/session_*.json` and terminal output

See `QUOTA_TROUBLESHOOTING.md` for detailed diagnosis.
