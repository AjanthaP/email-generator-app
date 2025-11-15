# AI Email Assistant

AI-powered email generation assistant built with FastAPI, React, and LangGraph. Generate professional emails with customizable tone, personalization, and context awareness.

## 🚀 Deployment

This project uses a **two-app architecture**:

### Backend (FastAPI) → Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

**Guide:** [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

### Frontend (React + Vite) → Vercel/Netlify/Railway

**Guide:** [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)

**Recommended Stack:**
- 🔧 **Backend:** Railway (Python/FastAPI with Docker)
- 🎨 **Frontend:** Vercel (React/Vite - optimized static hosting)
- 💾 **Database:** Railway Redis + MongoDB Atlas (optional)

## Quick start

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your API keys.

4. Run the FastAPI backend locally (after setting `GEMINI_API_KEY` in `.env`):

```powershell
uvicorn src.api.main:app --reload --port 8001
```

### Backend API (FastAPI)

We now expose the workflow as a REST API for use with a React (or any web) frontend.

1. Install dependencies (already included in `requirements.txt`).
2. Launch the API server:

```powershell
uvicorn src.api.main:app --reload --port 8001
```

The default CORS settings allow requests from `localhost:5173` and `localhost:3000`, which match the typical Vite and Create React App dev servers.

### React Frontend

- Scaffold a React app in `frontend/` (Vite recommended) and configure it to call `http://localhost:8001/email/generate`.
- Implement authentication pages and OAuth redirects using React Router (paths such as `/auth/callback`).
- **Developer Mode Implementation:** See [REACT_DEVELOPER_MODE.md](REACT_DEVELOPER_MODE.md) for complete guide on adding step-by-step workflow visibility with UI components, API integration, and best practices.

### Developer Mode (Per-step Outputs)

**For React Frontend:** Complete implementation guide available in [REACT_DEVELOPER_MODE.md](REACT_DEVELOPER_MODE.md)

**Python API:**
```python
from src.workflow.langgraph_flow import generate_email

result = generate_email(
    user_input="Write a follow-up email...",
    developer_mode=True  # Enable step-by-step capture
)
# result["developer_trace"] contains ordered list of {agent, snapshot}
```

**REST API:**
```bash
curl -X POST http://localhost:8001/email/generate \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a follow-up email...", "developer_mode": true}'
```

The trace shows post-step state for each agent (input_parser, intent_detector, draft_writer, tone_stylist, personalization, review, refinement, router) including `parsed_data`, `intent`, `draft`, `personalized_draft`, and `final_draft` fields.

## Repository Layout

Runtime vs non-runtime files are now separated clearly:

## Repository Layout

### React Frontend Roadmap

- Scaffold a React app in `frontend/` (Vite recommended) and configure it to call `http://localhost:8001/api/v1/email/generate`.
- Implement authentication pages and OAuth redirects using React Router (paths such as `/auth/callback`).
- Add a "Developer Mode" toggle to surface per-agent workflow trace returned by `generate_email(..., developer_mode=True)`.
- Render each agent snapshot (parsed input, intent, draft variants, final draft) above the draft history panel.

### Developer Mode (Per-step Outputs)

- Streamlit UI: enable `Developer mode (show step-by-step)` in the sidebar before generating. The app will display an expandable panel listing each agent and the output it produced at that step.
- Python API: call `generate_email(user_input, developer_mode=True)` (or use `execute_workflow(..., developer_mode=True)` if you need the full state). The returned dict includes `developer_trace`, an ordered list of `{ agent, snapshot }`.
- Notes: The trace shows the post-step state (e.g., `parsed_data`, `intent`, `draft`, `personalized_draft`, `final_draft`). This reflects the LLM’s effect per step without exposing provider-internal metadata.

## Repository Layout

Runtime vs non-runtime files are now separated clearly:

| Path | Purpose |
|------|---------|
| `src/` | Production backend source (FastAPI, agents, workflow) |
| `tests/` | Pytest test suite (unit & integration) |
| `scripts/diagnostics/` | One-off environment & data inspection scripts (not deployed) |
| `scripts/migration/` | Data migration helpers (placeholder) |
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

## 🚢 Deployment

### Railway (Recommended)

1. **Quick Check:**
   ```bash
   python check_railway.py
   ```

2. **Deploy:**
   - Push to GitHub
   - Connect Railway to your repository
   - Add environment variables (see `.env.railway`)
   - Railway auto-deploys!

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete guide.

### Other Platforms

- **Docker:** Use provided `Dockerfile`
- **Heroku:** Compatible with Procfile
- **AWS/Azure:** Deploy container or use app services

## 📝 Environment Variables

Required for production:
- `GEMINI_API_KEY` - Google Gemini API key
- `JWT_SECRET_KEY` - Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - For OAuth

See `.env.railway` for complete production configuration.

## 🏗️ Architecture

```
Frontend (React) ←→ Backend (FastAPI) ←→ LangGraph Workflow
                         ↓
                    Redis Cache
                         ↓
                    ChromaDB (optional)
```

---

Created from `email_assistant_guide_v2.md` project setup section.
Railway deployment configured for production use.