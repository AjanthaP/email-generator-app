# AI Email Assistant

AI-powered email generation assistant built with FastAPI, React, and LangGraph. Generate professional emails with customizable tone, personalization, and context awareness.

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.

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

4. Run the Streamlit UI (after setting `GEMINI_API_KEY` in `.env`):

```powershell
streamlit run src/ui/streamlit_app.py
```

### Backend API (FastAPI)

We now expose the workflow as a REST API for use with a React (or any web) frontend.

1. Install dependencies (already included in `requirements.txt`).
2. Launch the API server:

```powershell
uvicorn src.api.main:app --reload --port 8001
```

The default CORS settings allow requests from `localhost:5173` and `localhost:3000`, which match the typical Vite and Create React App dev servers.

### React Frontend Roadmap

- Scaffold a React app in `frontend/` (Vite recommended) and configure it to call `http://localhost:8001/api/v1/email/generate`.
- Implement authentication pages and OAuth redirects using React Router (paths such as `/auth/callback`).
- Replace Streamlit UI pieces incrementally by reusing the existing API endpoints for prompts, templates, history, and profiles.
- Once complete, Streamlit can be kept for internal tooling or removed.

## Files created
- `src/` — source package
- `tests/` — test package
- `data/templates/` — email templates
- `frontend/` — React frontend application
- `requirements.txt`, `.env.example`, `.gitignore`
- **Railway deployment files:**
  - `Dockerfile` — Container configuration
  - `railway.json` — Railway deployment settings
  - `.dockerignore` — Docker build exclusions
  - `start.py` — Production startup script
  - `RAILWAY_DEPLOYMENT.md` — Deployment guide

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