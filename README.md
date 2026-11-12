# AI Email Assistant

AI-powered email generation assistant: a FastAPI backend that runs a sequential multi-agent pipeline on Google Gemini (via LangChain), a React (Vite) frontend, and a Gmail/Outlook browser extension. It produces personalized emails with controllable tone, length targeting, and a per-agent developer trace.

> **Current status (November 2026)**
> - **Backend:** Google Cloud Run, service `email-generator-app` in region `asia-south1`, at https://email-generator-app-956218235973.asia-south1.run.app
> - **Frontend:** Vercel, at https://email-generator-app-frontend.vercel.app
> - **LLM:** Google Gemini. The default model is `gemini-3.5-flash-lite` (production uses it too); override it with `GEMINI_MODEL`.
> - **Database:** not connected in production yet. `DATABASE_URL` is not set on the Cloud Run service, so drafts, profiles and sessions use the JSON fallback inside the container. Cloud Run storage is temporary, so this data is lost whenever an instance restarts or a new revision is deployed. The PostgreSQL database from the earlier Railway setup still exists but is not wired to Cloud Run.
> - **Not used in production:** Redis, ChromaDB and MongoDB. They remain optional feature flags.
> - **Railway hosting is retired.** `railway.json`, `.github/workflows/railway-deploy.yml` and the Railway guides in `docs/guides/` are leftovers from that setup.

## ✅ Core Features
- Sequential multi-agent pipeline (parse → intent → draft → tone styling → personalization → review → routing)
- Precise word-length targeting (±5% tolerance; adaptive trimming only if necessary)
- Prompt-based review pass for tone, clarity, grammar and length (no hardcoded regex cleanup)
- Recipient & greeting preservation safeguards
- Personalization with profile-aware signature injection (no placeholders)
- Developer Mode trace: per-agent post-step snapshots
- Graceful LLM quota fallback to stubbed local generator
- Centralized prompt templates (single source of truth)
- Google and GitHub OAuth sign-in
- Gmail/Outlook browser extension and an MCP (Model Context Protocol) endpoint

## 🗺️ High-Level Architecture
```
React frontend (Vercel) ──┐
Browser extension ────────┼── HTTPS ──▶ FastAPI backend (Google Cloud Run, asia-south1)
MCP clients ──────────────┘               │
                                          ├─ Sequential agent pipeline (src/workflow/pipeline.py)
                                          │    InputParser → IntentDetector → DraftWriter → ToneStylist
                                          │    → Personalization → Review → Router
                                          │
                                          ├─ Google Gemini via langchain-google-genai
                                          │
                                          ├─ PostgreSQL via DATABASE_URL (not connected in production yet)
                                          │
                                          └─ JSON fallback under data/ (used in production today; temporary on Cloud Run)
```

`pipeline.py` (formerly `langgraph_flow.py`) is a plain sequential loop over the agents, not a LangGraph graph.

Optional, currently unused: Redis cache, ChromaDB vector store, MongoDB alternative persistence.

## 🚀 Deployment

This project uses a **two-app architecture**: the backend on Google Cloud Run and the frontend on Vercel.

### Backend (FastAPI) → Google Cloud Run
- The container image is built from `Dockerfile` (Python 3.11). The app listens on `$PORT`, which Cloud Run sets automatically.
- To redeploy from the repo root, keep the same service name and region so the URL doesn't change:

```bash
gcloud run deploy email-generator-app --source . --region asia-south1
```

- Configuration comes from environment variables on the Cloud Run service (see [Environment Variables](#-environment-variables-key)). Keep API keys and OAuth secrets in Secret Manager rather than plain env vars:

```bash
gcloud run services update email-generator-app --region asia-south1 \
  --update-secrets GEMINI_API_KEY=<secret-name>:latest
```

- To connect the database, set `DATABASE_URL` on the service. Existing JSON drafts are copied into PostgreSQL the first time a user's history is loaded, and `scripts/migrate_json_to_postgres.py` can migrate in bulk.
- Verify a deploy:

```bash
curl https://email-generator-app-956218235973.asia-south1.run.app/health
# {"status":"ok","app_name":"AI Email Assistant","version":"1.0.0"}
```

- The interactive API docs (`/docs`, `/redoc`) are only served when `DEBUG=true`, so they're off in production.

### Frontend (React + Vite) → Vercel
- Vercel deploys from the separate `email-generator-app-frontend` repository. The `frontend/` folder here is pushed there with `scripts/sync-frontend.ps1`; see [FRONTEND_SYNC_GUIDE.md](docs/guides/FRONTEND_SYNC_GUIDE.md).
- `VITE_API_BASE_URL` must be the Cloud Run URL. It's set in the Vercel project's environment variables, which take priority over `.env` files at build time. `frontend/.env.production` in this repo still holds the old Railway URL; the live site uses the Vercel setting.
- CORS: the backend allows the Vercel production domain by default, plus any `*.vercel.app` preview domain and Chrome/Firefox extension origins. Add more with `CORS_ORIGINS` or `FRONTEND_URL`.

### Browser Extension (Gmail / Outlook)
- Source is in `browser-extension/`; it calls `/api/extension/generate`, `/api/extension/usage` and `/api/extension/health`.
- Set `API_BASE_URL` in `browser-extension/background/service-worker.js` to `https://email-generator-app-956218235973.asia-south1.run.app/api` for production, or `http://localhost:8000/api` for local work. See [EXTENSION_QUICK_REFERENCE.md](docs/guides/EXTENSION_QUICK_REFERENCE.md).

## 🏁 Quick Start (Local)

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`. `DATABASE_URL` is optional; without it the app uses JSON files under `data/`.

4. Run the backend on port 8000, which is what the frontend expects locally (`frontend/.env.development`):

```powershell
uvicorn src.api.main:app --reload --port 8000
```

5. Run the frontend in a second terminal (opens on http://localhost:5173):

```powershell
cd frontend
npm install
npm run dev
```

## 🔌 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| GET | `/` | Service info |
| POST | `/api/email/generate` | Generate an email (body: `prompt`, plus optional `user_id`, `tone`, `recipient`, `recipient_email`, `length_preference`, `developer_mode`, `use_stub`, `save_to_history`, `reset_context`) |
| POST | `/api/email/regenerate` | Regenerate a draft |
| GET, PUT | `/api/users/{user_id}/profile` | Read or update a user profile |
| GET | `/api/users/{user_id}/history` | Draft history |
| POST | `/api/users/{user_id}/history/learn` | Learn preferences from an edited draft |
| GET | `/api/auth/providers` | Enabled OAuth providers (production: Google, GitHub) |
| POST | `/api/auth/start`, `/api/auth/exchange`, `/api/auth/logout` | OAuth sign-in flow |
| GET | `/api/auth/callback`, `/api/auth/callback/{provider}` | OAuth callbacks |
| POST, GET | `/api/extension/generate`, `/api/extension/usage`, `/api/extension/health` | Browser extension |
| GET, POST | `/api/mcp` | MCP JSON-RPC endpoint |
| GET | `/api/mcp/tools` | List MCP tools |
| GET | `/api/debug/profile/{user_id}` | Only when `DEBUG=true` |

### Developer Mode (Per-Step Trace)
Returns ordered snapshots after each agent with keys: `parsed_data`, `intent`, `draft`, `personalized_draft`, `final_draft`, `metadata`.

Python:
```python
from src.workflow.pipeline import generate_email
result = generate_email("Follow up about proposal", developer_mode=True)
for step in result["developer_trace"]:
      print(step["agent"], step["snapshot"].keys())
```
REST:
```bash
curl -s -X POST http://localhost:8000/api/email/generate \
   -H "Content-Type: application/json" \
   -d '{"prompt": "Follow up about proposal", "developer_mode": true}' | jq
```

## 📁 Repository Layout

| Path | Purpose |
|------|---------|
| `src/` | Backend source (FastAPI app, agents, workflow, auth, integrations) |
| `tests/` | Pytest test suite |
| `frontend/` | React (Vite) app; mirrored to `email-generator-app-frontend` for Vercel |
| `browser-extension/` | Gmail/Outlook extension |
| `scripts/` | Database setup and migration (`setup_database.py`, `migrate_json_to_postgres.py`, `db_inspect.py`), `setup_auth.py`, PowerShell helpers (`sync-frontend.ps1`, `start-extension-test.ps1`) and `diagnostics/` |
| `data/` | Local JSON fallback storage |
| `docs/` | Setup and feature guides (`docs/guides/`), Mermaid diagrams (`docs/diagrams/`), and notes (LangSmith analysis, demo video, enhancements) |
| `examples/` | Usage examples |
| `Dockerfile`, `.dockerignore` | Container image used by Cloud Run |
| `start.py` | Alternative local launcher (not used by the Dockerfile) |
| `railway.json`, `.github/workflows/railway-deploy.yml` | Legacy Railway config |
| `scripts/legacy/` | Older standalone check scripts, kept for reference |

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
pytest tests -q --ignore=tests/test_generate_with_tracing.py --continue-on-collection-errors
```
`tests/test_generate_with_tracing.py` is a standalone script that calls `sys.exit()` at import, which aborts the whole pytest run, so it's skipped. Three test files currently fail to load (`test_agents_structure.py`, `test_langsmith_config.py`, `test_refinement_agent.py`); the flag lets the rest run.

CI (`.github/workflows/railway-deploy.yml`) only runs on pushes to `main` and `dev_fastapi` and on pull requests to `main`, so it doesn't run for `master`, the default branch. It also ignores test failures (`|| true`).

## 📐 Length Targeting
- `length_preference` passed from UI becomes `effective_length` (minimum 25 if <10 requested).
- Agents aim for target word count; final adaptive trim only if >105%.
- Metadata records: `requested_length_preference`, `effective_length_preference` (if adjusted), `original_word_count`, `final_word_count`, `length_trimmed`.

## 🔒 Persistence Strategy
Primary: PostgreSQL when `DATABASE_URL` is set. Fallback: JSON under `data/` when it isn't (the current production setup) or when the database is unavailable.
Draft history normalized to always expose both `content` and `draft` keys for backward compatibility.

## 🧠 Agents Overview
1. InputParser – extract recipient, purpose, key points.
2. IntentDetector – classify into predefined intents.
3. DraftWriter – generate initial draft (no placeholders).
4. ToneStylist – apply tone guidelines without altering greeting.
5. Personalization – inject profile; safeguard recipient/greeting.
6. Review – check tone, clarity, grammar, completeness and length (±5%), and return an improved draft without changing the greeting or recipient. Refinement used to be a separate agent and is now part of this step; the old `REFINEMENT_AGENT_PROMPT` in `src/utils/prompts.py` is no longer used.
7. Router – check the final state and decide continue, retry or fallback. It uses fixed rules unless `ENABLE_LLM_ROUTER=true`, which asks Gemini instead. The pipeline doesn't act on `retry` yet; a retry loop capped by `ROUTER_MAX_RETRIES` (default 2) is planned in [TODO.md](TODO.md). A `fallback` decision replaces the draft with a basic template.

## 🔧 Environment Variables (Key)
| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Google Generative AI access (required) |
| `GEMINI_MODEL` | Gemini model name (default `gemini-3.5-flash-lite`; `gemini-2.0-*` models were shut down on June 1, 2026). Update `PRICE_INPUT_PER_MILLION` / `PRICE_OUTPUT_PER_MILLION` if you change it. |
| `DATABASE_URL` | PostgreSQL connection string (`postgresql://user:pass@host:port/db`); unset means JSON fallback |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | Google OAuth. The redirect URI must match what's registered in Google Cloud Console (the default points at localhost). |
| `ENABLE_GITHUB_OAUTH`, `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` / `GITHUB_REDIRECT_URI` | GitHub OAuth (enabled in production) |
| `CORS_ORIGINS`, `FRONTEND_URL` | Extra allowed frontend origins |
| `DEBUG` | Enables `/docs`, `/redoc` and `/api/debug/*` (keep `false` in production) |
| `LOG_LEVEL` | Logging level (default `INFO`) |
| `LOG_FORMAT` | `json` (default; one JSON object per line for Cloud Logging) or `text` |
| `TELEMETRY_SINKS` | Where telemetry events go: `auto` (default: stdout on Cloud Run, stdout + `data/metrics/events-*.jsonl` elsewhere), `log`, `file`, `log,file`, `none` |
| `ENABLE_FAULTS`, `FAULTS` | Fault injection for the triage eval (`src/utils/faults.py`). Local only: always off on Cloud Run. |
| `ENABLE_LLM_ROUTER` | Let the Router agent ask Gemini for its decision (default `false`; adds one call per request). See the Router notes under Agents Overview before turning it on. |
| `DONOTUSEGEMINI` or `NO_GEMINI` | Force stub (local) mode when truthy |
| `ENABLE_LANGSMITH`, `LANGSMITH_API_KEY`, `LANGCHAIN_PROJECT` | Optional LangSmith tracing |
| `ENABLE_COST_TRACKING`, `ENABLE_RATE_LIMITER` | Optional LLM cost tracking and client-side rate limiting |

`JWT_SECRET_KEY` appears in the config and `.env` templates but isn't used by the code; sessions use random tokens.

Optional (not used in production): `REDIS_URL`, ChromaDB and MongoDB settings. See `.env.example` for the full list.

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

The examples below use the local server; replace `http://localhost:8000` with the Cloud Run URL to call production.

Initialize
```powershell
curl -s -X POST http://localhost:8000/api/mcp `
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
curl -s -X POST http://localhost:8000/api/mcp `
      -H "Content-Type: application/json" `
      -d '{
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/list"
      }'
```

Call `generate_email`
```powershell
curl -s -X POST http://localhost:8000/api/mcp `
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
- The ToneStylist, Personalization and Review prompts instruct the model to keep the greeting line and recipient name exactly as drafted.
- The Personalization prompt forbids placeholder text such as `[Your Name]` and omits empty profile fields.
- Review and Personalization keep the email within ±5% of the target length.

---

Created from the original [`email_assistant_guide_v2.md`](docs/guides/email_assistant_guide_v2.md) and updated to match the current production setup (Cloud Run + Vercel + Gemini; database not yet connected; Redis/Chroma unused). Suggestions & contributions welcome.
