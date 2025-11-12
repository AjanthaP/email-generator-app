# AI Email Assistant

This is the starter scaffold for the AI-Powered Email Assistant project. The repository follows the structure described in the project guide and includes a minimal set of files to get started.

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
- `requirements.txt`, `.env.example`, `.gitignore`

---

Created from `email_assistant_guide_v2.md` project setup section.