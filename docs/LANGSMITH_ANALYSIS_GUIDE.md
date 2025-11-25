# 🔍 LangSmith Tracing Analysis Guide

## What LangSmith Logs

LangSmith automatically traces:
1. **LLM Calls** - Every time `chain.invoke()` is called
2. **Inputs & Outputs** - Full prompt text and responses
3. **Token Usage** - Input/output tokens per call
4. **Latency** - Time taken for each operation
5. **Error Details** - Stack traces and error messages
6. **Chain Structure** - How prompts are composed (prompt templates + LLM)

---

## Current Logging Status

### ✅ What's Being Traced
- All agent LLM calls via `llm_wrapper.invoke_chain()`
- Chain invocations: `prompt | llm`
- Token counts and latency (from Gemini API)
- Retry attempts and errors

### ❌ What's NOT Being Traced (Yet)
- **Agent-specific tags** (e.g., "input_parser", "draft_writer")
- **Custom metadata** (user_id, tone, length_preference)
- **Run names** (traces appear as generic "ChatPromptTemplate")
- **Parent-child relationships** (pipeline visualization)

---

## How to View Traces in LangSmith

### Step 1: Access Dashboard
1. Go to https://smith.langchain.com/
2. Click **Projects** in left sidebar
3. Find project: `email-generator`
4. Click to see all traces

### Step 2: Generate a Test Request
```bash
# From frontend (http://localhost:5173)
User Input: "Write a thank you email to Sarah"
Tone: Professional
Length: 100 words
```

### Step 3: Wait for Trace to Appear
- **Latency:** Typically **5-15 seconds** after request completes
- **Why the delay?** LangSmith buffers traces for efficiency
- **Refresh** the dashboard if traces don't appear immediately

### Step 4: Analyze the Trace
Click on a trace to see:
- **Overview**: Total time, tokens, cost
- **Trace Tree**: Sequence of LLM calls
- **Inputs**: Full prompt sent to Gemini
- **Outputs**: LLM response
- **Metadata**: Model, temperature, etc.

---

## Understanding Current Trace Output

### What You'll See Now (Without Tags)
```
ChatPromptTemplate
├─ Input: {"user_input": "Write..."}
└─ Output: AIMessage(content="...")
   Duration: 1.2s
   Tokens: 450 in / 280 out
```

### Expected Trace Count Per Email Generation
- **InputParser**: 1 trace
- **IntentDetector**: 1 trace
- **DraftWriter**: 1 trace
- **ToneStylist**: 1 trace (if tone styling applied)
- **Personalization**: 1 trace (if profile exists)
- **ReviewAgent**: 0 traces (validation only)
- **RefinementAgent**: 1-3 traces (depends on length adjustments)

**Total: 5-8 traces** per email generation

---

## Troubleshooting: "I Don't See Traces"

### Issue 1: Traces Not Appearing
**Possible Causes:**
1. ✅ **Wait longer** - Can take up to 30 seconds
2. ❌ **Wrong project** - Check you're viewing `email-generator` project
3. ❌ **API key mismatch** - Verify `.env` has correct `LANGSMITH_API_KEY`
4. ❌ **Tracing disabled** - Check `ENABLE_LANGSMITH=true` in `.env`
5. ❌ **Backend not restarted** - Restart uvicorn after `.env` changes

**Verification:**
```bash
# Check if tracing is active
python tests/test_langsmith_config.py

# Should show:
# ✓ LANGCHAIN_TRACING_V2: true
# ✓ LANGCHAIN_PROJECT: email-generator
```

### Issue 2: Traces Appear But Are Generic
**This is normal!** Current implementation doesn't add custom tags.

**To see which agent created which trace:**
- Look at the **Input** tab
- Check prompt content (e.g., "Parse the following user input..." = InputParser)

### Issue 3: Multiple Projects Showing
- LangSmith creates a project per `LANGCHAIN_PROJECT` env var
- Make sure all environments use `email-generator`
- Old test runs may show in `default` project

---

## Key Metrics to Track

### Performance Metrics
| Metric | Target | What It Means |
|--------|--------|---------------|
| **Total Latency** | < 5s | End-to-end pipeline time |
| **Avg per Agent** | < 1s | Individual agent efficiency |
| **Token Usage** | 800-1500 | Cost per email generation |
| **Error Rate** | < 1% | Reliability measure |

### Cost Analysis
- **Gemini Flash pricing**: ~$0.00015 per 1k tokens (varies by region)
- **Average email cost**: $0.001 - $0.002 (1-2 cents per 1000 emails)
- Check **Monitoring** tab in LangSmith for cumulative costs

---

## Example: Reading a Trace

### Scenario: User generates professional email

**Trace 1: InputParser**
```
Input:
{
  "user_input": "Write a thank you email to Sarah for the presentation"
}

Prompt Sent to Gemini:
Parse the following user input and extract...
[user_input]: Write a thank you email to Sarah for the presentation

Output:
{
  "recipient": "Sarah",
  "subject": "Thank You for the Presentation",
  "context": "appreciation for presentation"
}

Metadata:
- Model: gemini-2.0-flash
- Tokens: 125 in / 45 out
- Latency: 0.8s
- Cost: $0.000026
```

**Trace 2: DraftWriter**
```
Input:
{
  "recipient": "Sarah",
  "subject": "Thank You for the Presentation",
  "context": "appreciation for presentation",
  "tone": "professional"
}

Output:
Subject: Thank You for the Presentation

Dear Sarah,

I wanted to express my sincere gratitude...

Metadata:
- Tokens: 320 in / 180 out
- Latency: 1.4s
- Cost: $0.000075
```

---

## Advanced: Adding Custom Tags (Future Enhancement)

To make traces more useful, we could add tags to each agent call:

```python
# In llm_wrapper.py
def invoke_chain(self, chain: Any, params: dict, tags: list[str] = None, **retry_kwargs):
    config = {"tags": tags or []} if tags else {}
    result = self.run_with_retries(lambda: chain.invoke(params, config=config))
```

Then in agents:
```python
# In input_parser.py
response = self.llm_wrapper.invoke_chain(
    chain, 
    {"user_input": user_input},
    tags=["input_parser", "parsing", user_id]
)
```

This would make traces filterable by agent type in LangSmith.

---

## Quick Reference Commands

```bash
# Test LangSmith config (no API calls)
python tests/test_langsmith_config.py

# Test full pipeline with tracing
python tests/test_langsmith_trace.py

# Check backend logs for tracing activation
# Look for: "LangSmith tracing activated with personal API key"

# Restart backend to pick up .env changes
# Ctrl+C in python terminal, then re-run uvicorn command
```

---

## Expected Timeline

1. **T+0s**: User submits email request
2. **T+1-4s**: Backend processes through agent pipeline
3. **T+4s**: Response sent to frontend
4. **T+5-15s**: Traces appear in LangSmith dashboard
5. **T+20-30s**: All metrics and costs fully calculated

---

## Common Questions

**Q: Why do traces take so long to appear?**  
A: LangSmith batches traces for efficiency. The SDK sends traces asynchronously after the request completes.

**Q: Can I see real-time traces?**  
A: Not directly. Best approach is to refresh LangSmith every 5-10 seconds after making a request.

**Q: What if I see errors in traces?**  
A: Click the trace → **Error** tab shows full stack trace and error message. This is invaluable for debugging LLM failures.

**Q: How do I filter traces by time?**  
A: Use the date picker in top-right of LangSmith project view. Default shows last 24 hours.

**Q: Can I compare two traces side-by-side?**  
A: Yes! Check boxes next to traces → Click **Compare** button at top. Shows diff of inputs/outputs.

---

## Next Steps

1. ✅ **Run test**: `python tests/test_langsmith_config.py`
2. ✅ **Generate email** via frontend
3. ✅ **Wait 15 seconds**
4. ✅ **Check LangSmith**: https://smith.langchain.com/
5. ✅ **Look for project**: `email-generator`
6. ✅ **Click a trace** to explore details
