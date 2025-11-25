# Email Generator App — Demo Walkthrough Guide

This guide highlights the key files and the end-to-end flow so you can explain how the app works during a demo. It’s short, scannable, and references concrete code paths in this repo.

## Core Flow (Backend)
- `src/utils/config.py`: Central settings (Gemini model/key, Chroma toggles, DB URLs, CORS). All agents read from here via `settings`.
- `src/workflow/langgraph_flow.py`: Orchestrates the main generation pipeline: InputParser → IntentDetector → DraftWriter → ToneStylist → Personalization → Review. Returns a `state` containing `final_draft`, `metadata`, and optional `developer_trace`.
- `src/api/routers/email.py`: REST endpoints.
  - `POST /api/email/generate`: Calls `execute_workflow(...)`, saves draft (if requested), returns `EmailGenerateResponse` with `draft`, `metadata`, `metrics`.
  - `POST /api/email/regenerate`: Adaptive re-polish based on diff ratio.
    - <20% change → Review-only (fast).
    - ≥20% change → Tone → Personalization → Review (full polish).
- `src/memory/memory_manager.py`: Persistence abstraction.
  - Uses PostgreSQL when configured; falls back to JSON under `data/drafts`.
  - After saving a draft, triggers async vector indexing (Chroma) with content and metadata.

## Agents (LLM Workers)
- `src/agents/draft_writer.py`: Writes a first draft using intent-specific prompts (e.g., outreach, follow_up). Uses `{target_length}` to control verbosity.
- `src/agents/tone_stylist.py`: `adjust_tone(draft, tone)` rewrites with tone constraints while preserving greeting and recipient.
- `src/agents/personalization.py`: Pulls profile (DB or JSON), injects signature and style, and now queries top-3 similar past drafts from Chroma to build `reference_context` for the LLM.
- `src/agents/review.py`: Final reviewer/refiner. Ensures tone/length/clarity and outputs `final_draft`.
- `src/agents/router.py`: Optional LLM-based router for continue|retry|fallback decisions, controlled by `settings.enable_llm_router`.

## Prompts
- `src/utils/prompts.py`:
  - `INPUT_PARSER_PROMPT`, `INTENT_DETECTOR_PROMPT` → early understanding.
  - `TONE_STYLIST_PROMPT`, intent templates → generation and tone.
  - `PERSONALIZATION_PROMPT` → now accepts `{reference_context}`; instructs to use past examples as style-only, no leakage.
  - `REVIEW_AGENT_PROMPT` → final polish; maintain greeting/recipient and word budget.

## Vector Personalization (Chroma)
- `src/utils/vector_store.py`:
  - Persistent Chroma client at `data/chromadb` (default).
  - Embeddings via Gemini `text-embedding-004` (falls back to default embeddings if unavailable).
  - `index_draft_async(user_id, draft_id, content, metadata)` called after saves.
  - `query_similar(user_id, query_text, k=3)` for top-3 similar drafts.
- How it flows:
  1) Generate → save draft.
  2) Background thread embeds + upserts document into Chroma.
  3) Personalization queries by current draft text; builds `reference_context` shown to the LLM.

## Persistence
- DB Models (Postgres): `src/db/models.py` defines `Draft` and `UserProfile`.
- JSON fallback: `data/drafts/{user}_drafts.json` and `data/profiles`.
- Chroma index: `data/chromadb` (safe to delete to reset; it will rebuild).

## Frontend (high-level)
- React/Vite app (not detailed here) calls `/api/email/generate` and `/api/email/regenerate`.
- Regenerate UI tracks original vs edited; backend uses diff to choose lightweight vs full path.

## Configuration & Env
- Required: `GEMINI_API_KEY`.
- Optional overrides (defaults cover most demos):
  - `CHROMA_PERSIST_DIR=./data/chromadb`
  - `CHROMA_COLLECTION=email_drafts`
  - `ENABLE_VECTOR_INDEXING=true`
  - `TOP_K_SIMILAR=3`
  - `SIMILARITY_THRESHOLD=0.6`

## Demo Talking Points
- Start-to-finish: prompt → intent & draft → tone → personalization (with history) → review.
- Safety/consistency: preserve greeting/recipient; avoid placeholders; enforce target length.
- Personalization depth: profile + vector recall of similar emails for style alignment.
- Performance: adaptive regenerate avoids running the full chain for small edits.
- Observability: `metadata`, `metrics.session_summary()`, and optional developer traces.

## Quick Commands (Windows PowerShell)
```powershell
# Backend (ensure env set for Gemini key)
$env:GEMINI_API_KEY = "<your_key>"; python -m uvicorn src.main:app --reload --port 8000

# Hit generate
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/email/generate" -ContentType "application/json" -Body (@{
    prompt = "Write a follow-up to John about the proposal";
    tone = "formal";
    user_id = "demo-user";
    save_to_history = $true
} | ConvertTo-Json)

# After a couple generates, try regenerate with a small edit (lightweight path)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/email/regenerate" -ContentType "application/json" -Body (@{
    original_draft = "...original...";
    edited_draft = "...small edit...";
    tone = "formal";
    user_id = "demo-user"
} | ConvertTo-Json)
```

Tip: Show `data/chromadb` appearing after the first save and mention async indexing to explain non-blocking UX.
