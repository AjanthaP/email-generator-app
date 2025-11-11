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

## Files created
- `src/` — source package
- `tests/` — test package
- `data/templates/` — email templates
- `requirements.txt`, `.env.example`, `.gitignore`

---

Created from `email_assistant_guide_v2.md` project setup section.