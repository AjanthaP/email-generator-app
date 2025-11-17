# AI Email Assistant

AI-powered email generation assistant built with FastAPI, LangGraph, and a React (Vite) frontend. It produces professional, personalized emails with controllable tone, length targeting, and developer trace visibility.

> CURRENT STATUS (Nov 2025): Active components are FastAPI + Gemini (Google Generative AI) + PostgreSQL (Railway) + JSON local fallback storage + Agent workflow. Redis, ChromaDB, and MongoDB are NOT currently used in production; they remain optional feature flags for future expansion.

## ✅ Core Features
- Structured multi-agent workflow (parse → intent → draft → tone styling → personalization → review → refinement → routing)
- Precise word-length targeting (±5% tolerance; adaptive trimming only if necessary)
- Prompt-only refinement (no hardcoded regex cleanup)
- Recipient & greeting preservation safeguards
- Personalization with profile-aware signature injection (no placeholders)
- Developer Mode trace: per-agent post-step snapshots
- Graceful LLM quota fallback to stubbed local generator
- Centralized prompt templates (single source of truth)

## 🗺️ High-Level Architecture
```
React Frontend (Vite) ── REST calls ──▶ FastAPI Backend
                                         │
                                         ├─ LangGraph-inspired Sequential Agents
                                         │    (InputParser → Intent → DraftWriter → ToneStylist → Personalization → Review → Refinement → Router)
                                         │
                                         ├─ Google Gemini (LLM) via langchain-google-genai
                                         │
                                         ├─ PostgreSQL (Railway)  ← primary persistence (profiles, drafts)
                                         │
                                         └─ JSON fallback (data/ ) when DB unavailable
```

Optional / Future (currently disabled): Redis cache, ChromaDB vector store, MongoDB alternative persistence.

## 🚀 Deployment

This project uses a **two-app architecture** (backend + frontend).

### Backend (FastAPI) → Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
See: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

### Frontend (React + Vite) → Vercel / Netlify / Railway
See: [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)

**Recommended Stack (Current):**
- 🔧 Backend: Railway (FastAPI + Docker)
- 🎨 Frontend: Vercel (Vite React build output)
- 💾 Database: PostgreSQL on Railway
- 🧠 LLM: Google Gemini Flash (`gemini-2.0-flash`)
- 📂 Fallback Storage: Local JSON (`data/`)

## 🏁 Quick Start

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your API keys & `DATABASE_URL`.

4. Run the FastAPI backend locally (after setting `GEMINI_API_KEY` in `.env`):

```powershell
uvicorn src.api.main:app --reload --port 8001
```

### Backend API (FastAPI)
Exposes a workflow endpoint (`POST /email/generate`) and history/profile endpoints.

Run locally:
```powershell
uvicorn src.api.main:app --reload --port 8001
```
Default CORS allows `localhost:5173`, `localhost:3000`.

### React Frontend
- Vite-based React app under `frontend/` calls `http://localhost:8001/email/generate`.
- OAuth flows (Google) route via `/auth/callback` (see deployment guide).
- Developer Mode toggle surfaces per-agent trace (see below).

### Developer Mode (Per-Step Trace)
Returns ordered snapshots after each agent with keys: `parsed_data`, `intent`, `draft`, `personalized_draft`, `final_draft`, `metadata`.

Python:
```python
from src.workflow.langgraph_flow import generate_email
result = generate_email("Follow up about proposal", developer_mode=True)
for step in result["developer_trace"]:
      print(step["agent"], step["snapshot"].keys())
```
REST:
```bash
curl -s -X POST http://localhost:8001/email/generate \
   -H "Content-Type: application/json" \
   -d '{"user_input": "Follow up about proposal", "developer_mode": true}' | jq
```

## 📁 Repository Layout

| Path | Purpose |
|------|---------|
| `src/` | Production backend source (FastAPI, agents, workflow) |
| `tests/` | Pytest test suite (unit & integration) |
| `scripts/diagnostics/` | Local environment & data inspection scripts |
| `scripts/migration/` | Data migration helpers (future) |
| `data/` | Local JSON fallback storage & templates |
| `frontend/` | React application (not included in this repository if external) |
| `Dockerfile`, `railway.json`, `.dockerignore`, `start.py` | Deployment artefacts for Railway |
| `README.md`, `RAILWAY_DEPLOYMENT.md` | Documentation |

To run a diagnostic script (local only):
```bash
python scripts/diagnostics/check_drafts.py <user_id>
python scripts/diagnostics/test_draft_history.py
python scripts/diagnostics/database_url_fix.py
```
These scripts must NOT be invoked from production containers; they are excluded from runtime logic.

## 🧪 Testing
Run the test suite:
```powershell
pytest -q
```

## 📐 Length Targeting
- `length_preference` passed from UI becomes `effective_length` (minimum 25 if <10 requested).
- Agents aim for target word count; final adaptive trim only if >105%.
- Metadata records: `requested_length_preference`, `effective_length_preference` (if adjusted), `original_word_count`, `final_word_count`, `length_trimmed`.

## 🔒 Persistence Strategy
Primary: PostgreSQL (Railway). Fallback: JSON under `data/` if DB unavailable or during quota fallback.
Draft history normalized to always expose both `content` and `draft` keys for backward compatibility.

## 🧠 Agents Overview
1. InputParser – extract recipient, purpose, key points.
2. IntentDetector – classify into predefined intents.
3. DraftWriter – generate initial draft (no placeholders).
4. ToneStylist – apply tone guidelines without altering greeting.
5. Personalization – inject profile; safeguard recipient/greeting.
6. Review – polish, ensure quality & length alignment.
7. Refinement – ordered cleanup (dedupe, placeholders removal, grammar, subtle corrections) via prompt.
8. Router – finalize routing / next-step metadata.

## 🔧 Environment Variables (Key)
| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Google Generative AI access |
| `DATABASE_URL` | PostgreSQL connection string (`postgresql://user:pass@host:port/db`) |
| `JWT_SECRET_KEY` | Auth token signing (auto-generate if absent) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth login |
| `DONOTUSEGEMINI` or `NO_GEMINI` | Force stub (local) mode when truthy |

Optional (disabled by default in current deployment): `REDIS_URL`, Chroma config vars.

## 🧩 Optional / Planned Integrations
- Redis caching layer (rate limiting, draft cache)
- ChromaDB vector store for semantic context retrieval
- MongoDB alternative persistence
These remain behind feature toggles; none are active in production at present.

## 🔗 MCP (Model Context Protocol)
We expose a lightweight MCP-compatible JSON-RPC endpoint over HTTP to make tools and prompts available to external MCP clients.

- Endpoint: `POST /api/mcp` (JSON-RPC 2.0)
- Tools listing (convenience HTTP): `GET /api/mcp/tools`
- Server name: `email-generator-mcp-server`

Quick examples (PowerShell):

Initialize
```powershell
curl -s -X POST http://localhost:8001/api/mcp `
      -H "Content-Type: application/json" `
      -d '{
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
      }'
```

List tools
```powershell
curl -s -X POST http://localhost:8001/api/mcp `
      -H "Content-Type: application/json" `
      -d '{
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/list"
      }'
```

Call `generate_email`
```powershell
curl -s -X POST http://localhost:8001/api/mcp `
      -H "Content-Type: application/json" `
      -d '{
            "jsonrpc": "2.0",
            "id": "3",
            "method": "tools/call",
            "params": {
                  "name": "generate_email",
                  "arguments": {
                        "user_id": "default",
                        "prompt": "Follow up about the proposal we sent last week.",
                        "tone": "formal",
                        "context": {"developer_mode": true, "length_preference": 120}
                  }
            }
      }'
```

Notes:
- This HTTP transport is a pragmatic adapter; some MCP clients (e.g., Claude Desktop) prefer stdio transports. For those, wrap `POST /api/mcp` in a gateway or add a stdio transport.
- Tools implemented: `generate_email`, `get_email_templates`, `analyze_email_context`, `get_user_preferences`. Resources and prompts are also listed via MCP methods.

## 🩹 Quota / Failure Fallback
If Gemini quota error detected (429 / ResourceExhausted), system switches to stub state preserving workflow continuity; metadata marks source as `stub` and records fallback.

## 🛡️ Safety & Output Integrity
- Greeting and recipient name preserved exactly after initial generation.
- No placeholder tokens ever emitted post-personalization.
- Refinement prompt forbids fact invention, uncontrolled shortening, or new promises.

## 🚢 Deployment (Summary)
See detailed guides in `RAILWAY_DEPLOYMENT.md` and `FRONTEND_DEPLOYMENT.md`.
Docker image builds from `Dockerfile`; environment variables injected at deploy time. Ensure `DATABASE_URL` and `GEMINI_API_KEY` are set before first request.

---

Created from original `email_assistant_guide_v2.md` with live adjustments to reflect current production stack (PostgreSQL + Gemini; Redis/Chroma disabled). Suggestions & contributions welcome.