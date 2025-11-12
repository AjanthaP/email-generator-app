# Gemini Quota Troubleshooting Guide

## Why Am I Hitting Rate Limits With "Just 1 Request"?

### The Root Cause
When you click "Generate Email" **once**, the system makes **5-6 separate LLM API calls** behind the scenes:

1. **Input Parser** → Gemini API call #1
2. **Intent Detector** → Gemini API call #2  
3. **Draft Writer** → Gemini API call #3
4. **Tone Stylist** → Gemini API call #4
5. **Personalization** → Gemini API call #5
6. **Review Agent** → Gemini API call #6 (if enabled)

**Total: 6 LLM calls per email generation**, all happening in ~1-2 seconds.

### Gemini Free Tier Limits (gemini-2.0-flash-exp)
- **Requests per minute (RPM):** 2-15 (varies, experimental models have stricter limits)
- **Tokens per minute (TPM):** 1,000,000 (shared across all calls)
- **Requests per day:** 1,500

**Result:** Your 6 rapid calls exceed the RPM limit immediately → quota error → fallback to stub mode.

---

## How to Confirm This

### 1. Check the new metrics panel
After updating the code, the sidebar now shows:
- **LLM Calls** (not "Requests") — shows actual API call count
- **Successful** — how many succeeded
- **Errors** — how many failed (quota/429 errors)

Generate one email and you should see:
- LLM Calls: 6 (or 5 if review is skipped)
- Errors: 4-5 (quota kicked in after first 1-2 calls)

### 2. Enable debug logging
In `.env`:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

Restart Streamlit. Now check the terminal output—you'll see detailed logs showing:
```
DEBUG:src.utils.llm_wrapper:Attempting token extraction from result type: AIMessage
DEBUG:src.utils.llm_wrapper:Found response_metadata: ['token_count_total', 'token_count_prompt', ...]
DEBUG:src.utils.llm_wrapper:Extracted tokens: in=45, out=120
```

Or quota errors:
```
WARNING:src.utils.llm_wrapper:LLM call failed (attempt 1/3). Backing off for 1.0s
ERROR:... ResourceExhausted: 429 You exceeded your current quota
```

### 3. Flush metrics to disk
Click "💾 Flush Metrics to Disk" in the sidebar. Open the JSON file in `data/metrics/session_*.json`:
```json
{
  "session": {
    "llm_calls": 6,
    "successful_calls": 1,
    "errors": 5,
    "input_tokens": 245,
    "output_tokens": 0  // <-- if 0, token extraction failed
  },
  "calls": [
    {"model": "gemini-2.0-flash-exp", "latency_ms": 850, "input_tokens": 45, "output_tokens": 120, "error": null},
    {"model": "gemini-2.0-flash-exp", "latency_ms": 120, "input_tokens": 50, "output_tokens": 0, "error": "429 quota exceeded"},
    ...
  ]
}
```

---

## Solutions

### Option 1: Upgrade to Paid Tier (Recommended for Production)
**Gemini API Pay-As-You-Go** gives you:
- RPM: 300-1,000 (depending on model)
- TPM: 4,000,000
- Cost: ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens for Flash models

**To enable:**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Upgrade to paid billing
3. Your existing API key automatically gets higher limits

**Expected cost for your app:**
- 1 email = 6 calls × ~200 tokens/call = ~1,200 tokens
- 100 emails/day = 120,000 tokens ≈ **$0.01-0.02/day**

### Option 2: Switch to a Stable (Non-Experimental) Model
Experimental models (`-exp` suffix) often have stricter rate limits.

**Better alternatives:**
```env
GEMINI_MODEL=gemini-1.5-flash
```
or
```env
GEMINI_MODEL=gemini-1.5-flash-8k  # Even cheaper, same quality for short emails
```

Benefits:
- More generous free tier RPM (often 15 RPM vs 2 RPM for experimental)
- Stable pricing and availability
- Production-ready SLA

### Option 3: Enable Client-Side Rate Limiting
Add to `.env`:
```env
ENABLE_RATE_LIMITER=true
REQUESTS_PER_MINUTE=10
TOKENS_PER_MINUTE=50000
MAX_CONCURRENCY=2
```

This will:
- Throttle your 6 rapid calls to spread them over 6-12 seconds
- Stay under Gemini's quota
- Automatically retry with backoff

**Trade-off:** Email generation takes 10-15 seconds instead of 2 seconds.

### Option 4: Consolidate Agents (Advanced)
Reduce the number of LLM calls by combining agents:
- Merge Input Parser + Intent Detector → 1 call instead of 2
- Merge Draft Writer + Tone Stylist → 1 call instead of 2

**Implementation:**
Edit `src/workflow/langgraph_flow.py` to create a "super-prompt" that does multiple tasks in one shot.

**Trade-off:** Less modular code, harder to debug individual steps.

### Option 5: Use Stub Mode for Development
While developing/testing UI:
```env
DONOTUSEGEMINI=1
```

Or check "Use stub (no Gemini)" in the Streamlit sidebar. This gives you instant drafts with zero API calls.

---

## Why Output Tokens Show 0

If you see `Output Tokens: 0` but got a draft back, it means:
1. Token extraction from the Gemini response failed
2. The fallback estimator is not working (bug)

**To fix:** The latest code update adds debug logging. Check terminal output for:
```
DEBUG:src.utils.llm_wrapper:Found usage_metadata at top level: {'prompt_token_count': 45, 'candidates_token_count': 120, ...}
```

If you don't see this, the response structure changed. Share the debug logs and we'll update the extraction logic.

**Current known extraction paths (all tried):**
- `result.response_metadata['prompt_token_count']` / `['candidates_token_count']`
- `result.additional_kwargs['usage_metadata']['input_tokens']` / `['output_tokens']`
- `result.usage_metadata['prompt_token_count']` / `['candidates_token_count']`

---

## Recommended Configuration for Your Use Case

**For development (free tier):**
```env
GEMINI_MODEL=gemini-1.5-flash
ENABLE_RATE_LIMITER=true
REQUESTS_PER_MINUTE=10
DEBUG=True
```

**For production (paid tier):**
```env
GEMINI_MODEL=gemini-1.5-flash-8k
ENABLE_COST_TRACKING=true
ENABLE_LANGSMITH=true
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=email-assistant-prod
```

---

## Quick Checks

Run these to verify your setup:

### 1. Check your API key quota tier
```python
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Hello")
print(response.usage_metadata)  # Should show token counts
```

### 2. Test single agent in isolation
```python
from src.agents.draft_writer import DraftWriterAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import settings

llm = ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.gemini_api_key)
writer = DraftWriterAgent(llm)
result = writer.write("outreach", {"recipient_name": "Test", "email_purpose": "demo", "key_points": ["point 1"]}, "formal")
print(result)
```

If this succeeds, quota is fine. If it fails with 429, you're hitting rate limits.

---

## Still Having Issues?

1. **Flush metrics to disk** and share the JSON file
2. **Enable DEBUG logging** and share terminal output (first 50 lines after clicking Generate)
3. Check if your API key is restricted (GCP console → API Keys → check restrictions)
4. Try switching to `gemini-1.5-flash` to rule out experimental model issues

---

## Summary

**Your "1 request" is actually 6 API calls.** Gemini's free tier experimental model has very low RPM limits (2-5 requests/min). Either:
- Upgrade to paid (costs ~$0.01/day for 100 emails)
- Switch to `gemini-1.5-flash` (higher free tier limits)
- Enable rate limiting (slower but stays under quota)
- Consolidate agents (advanced, reduces calls to 2-3)

The updated metrics panel now shows the real LLM call count so you can see exactly what's happening.
