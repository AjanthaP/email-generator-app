# 🎬 Demo Video Guide - AI Email Generator

## Video Structure (5-7 minutes)

### **1. Introduction (30 seconds)**
- "AI-powered email generator with multi-agent workflow"
- Tech stack highlight: Google Gemini + PostgreSQL + Railway + React
- Show the landing page briefly

---

### **2. Core Feature Demo (2-3 minutes)**

#### **Scenario 1: Simple Professional Email**
```
User Input: "Write a follow-up email to Sarah about the quarterly report deadline"
```
- Show the input form
- **Highlight the pipeline in action:**
  - Split screen or overlay showing: Input Parser → Intent Detection → Draft Writer → Tone Stylist → Review
  - Use browser DevTools Network tab to show API calls
  - Point out real-time status updates if you have them

#### **Scenario 2: Tone Customization**
```
User Input: "Write a casual thank you email to my team for completing the project"
Tone: Casual → Formal (change it)
Length: Short (100 words)
```
- Generate with "casual" tone first
- Show the output
- **Change to "formal" tone** and regenerate
- **Compare both versions side-by-side** (screenshot or two browser windows)
- Highlight how the same request produces different results

---

### **3. Advanced Features (1-2 minutes)**

#### **Personalization Demo**
```
User Input: "Invite John to our product launch event next Friday"
```
- Show user profile integration (if you have saved preferences)
- Demonstrate how it pulls company name, role, or previous context

#### **Length Targeting**
```
User Input: "Explain our new pricing model to existing customers"
Length: 50 words → 200 words → 500 words
```
- Generate 3 versions
- Show how refinement agent adjusts content length while preserving message

#### **Validation & Review**
- Trigger a validation failure (e.g., unclear input: "Send email")
- Show error feedback: "Missing recipient and subject"
- Show how ReviewAgent catches issues (missing context, inappropriate tone)

---

### **4. Technical Highlights (1-2 minutes)**

#### **LangSmith Tracing Visualization**
- Open https://smith.langchain.com/
- Show a trace from the previous generation
- Highlight:
  - Each agent's execution time
  - LLM token usage per agent
  - Error handling/retries if any

#### **MCP Integration Demo** (Optional but impressive)
- Show the `/api/mcp` endpoint
- Run a curl command:
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "generate_email",
      "arguments": {
        "user_input": "Schedule meeting with Alex",
        "tone": "professional"
      }
    },
    "id": 1
  }'
```
- Show JSON response with generated email

#### **Database Persistence**
- Show PostgreSQL Railway dashboard
- Query to show stored user profiles/drafts
- Demonstrate how data persists across sessions

---

### **5. Fallback & Error Handling (1 minute)**

#### **Fallback Recovery Demo**
- Disconnect internet or simulate API failure
- Show graceful degradation (JSON fallback if implemented)
- Or show retry mechanism in action (check backend logs)

#### **Edge Cases**
```
User Input: "asdfghjkl" (gibberish)
```
- Show how IntentDetector handles unclear requests
- Demonstrate validation feedback

---

### **6. Closing (30 seconds)**
- Quick recap: "Multi-agent pipeline, customizable, observable"
- Show GitHub repo (optional)
- Mention scalability: Railway deployment ready

---

## 🎥 Production Tips

### **Screen Recording Setup:**
- **Tools:** OBS Studio (free) or Loom
- **Layout:** 
  - Main: Frontend (full screen)
  - Picture-in-picture: LangSmith traces OR backend logs
  - Use zoom/highlight for important elements

### **Make It Visual:**
- Add annotations/arrows pointing to "Intent Detected: Meeting Request"
- Use color-coded boxes around different agents
- Show a simple flowchart overlay when explaining pipeline

### **Script Key Points:**
1. "Notice how the IntentDetector classified this as a 'meeting request'"
2. "The ToneStylist agent rewrote this with formal language"
3. "ReviewAgent validated recipient and subject are present"
4. "LangSmith shows this took 2.3 seconds with 847 tokens"

### **What NOT to show:**
- Don't show API keys or credentials
- Skip long loading times (edit them out)
- Avoid dwelling on technical errors unless demonstrating recovery

---

## 📝 Demo Script Template

### Opening
> "Hi, I'm demonstrating an AI-powered email generator built with a multi-agent architecture. It uses Google Gemini, PostgreSQL, and deploys on Railway. Let's see it in action."

### Core Demo
> "I'll start with a simple request: 'Write a follow-up email to Sarah about the quarterly report deadline.' Watch as it flows through our pipeline—parsing the input, detecting intent, generating the draft, styling the tone, and finally reviewing for quality."

### Tone Change
> "Now let's see personalization. I'll ask for a casual thank you email, then switch to formal tone. Notice how the same content adapts to different professional contexts."

### Technical Deep Dive
> "Behind the scenes, LangSmith traces every agent's execution. Here you can see the InputParser took 0.3 seconds, the DraftWriter used 425 tokens, and the entire pipeline completed in under 3 seconds."

### Closing
> "This architecture makes email generation fast, customizable, and observable. The system is production-ready and deployed on Railway. Thanks for watching!"

---

## 🎯 Key Metrics to Highlight

- **Response Time:** < 5 seconds for full pipeline
- **Token Efficiency:** ~800-1200 tokens per email
- **Agent Success Rate:** Show validation passing
- **Personalization:** Demonstrate context awareness
- **Scalability:** Mention Railway auto-scaling

---

## 🔗 Resources to Show

1. Live frontend: http://localhost:5173
2. API endpoint: http://localhost:8000/api/mcp
3. LangSmith dashboard: https://smith.langchain.com/
4. Railway deployment (if available)
5. GitHub repository (optional)
