"""Email generation endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.memory.memory_manager import MemoryManager
from src.utils.metrics import metrics
from src.workflow.langgraph_flow import execute_workflow
from ..schemas import EmailGenerateRequest, EmailGenerateResponse

router = APIRouter()

_memory_manager = MemoryManager()


def _prepare_prompt(payload: EmailGenerateRequest) -> str:
    """Compose the workflow prompt including optional recipient context."""
    sections = []
    if payload.recipient:
        sections.append(f"Recipient: {payload.recipient}")
    if payload.recipient_email:
        sections.append(f"Recipient Email: {payload.recipient_email}")
    if payload.length_preference:
        sections.append(f"Length preference: {payload.length_preference}")
    sections.append(payload.prompt)
    return "\n\n".join(sections)


@router.post("/generate", response_model=EmailGenerateResponse)
async def generate_email(payload: EmailGenerateRequest) -> EmailGenerateResponse:
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    user_id = payload.user_id or "default"
    drafts_before_call = _memory_manager.load_drafts(user_id)
    had_history = bool(drafts_before_call)
    use_prior_context = had_history and not payload.reset_context

    full_prompt = _prepare_prompt(payload)

    try:
        state: Dict[str, Any] = await run_in_threadpool(
            execute_workflow,
            full_prompt,
            use_stub=payload.use_stub,
            user_id=user_id,
            tone=payload.tone or "formal",
            developer_mode=payload.developer_mode,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise HTTPException(status_code=500, detail=f"Workflow error: {exc}") from exc

    draft = (
        state.get("final_draft")
        or state.get("personalized_draft")
        or state.get("styled_draft")
        or state.get("draft")
    )

    if not draft:
        raise HTTPException(status_code=502, detail="Workflow did not return a draft")

    metadata: Dict[str, Any] = state.get("metadata", {})
    # Ensure tone in metadata reflects what was actually requested and processed
    final_tone = payload.tone or "formal"
    metadata.update(
        {
            "intent": state.get("intent"),
            "tone": final_tone,
            "recipient": state.get("recipient", payload.recipient),
            "model": metadata.get("model") or metadata.get("fallback_from_model"),
            "source": metadata.get("source", "llm"),
        }
    )

    context_mode = "contextual" if use_prior_context else "fresh"
    metadata["context_mode"] = context_mode
    if had_history:
        metadata.setdefault("context_available", len(drafts_before_call))

    review_notes = state.get("review_notes", {}) or {}
    saved = False

    if payload.save_to_history:
        try:
            _memory_manager.save_draft(
                user_id,
                {
                    "content": draft,
                    "draft": draft,  # For backward compatibility
                    "metadata": metadata,
                    "original_input": payload.prompt
                },
            )
            saved = True
        except Exception:  # pylint: disable=broad-exception-caught
            saved = False

    usage_summary = metrics.session_summary()
    last_call = metrics.last_call()
    if last_call:
        usage_summary["last_call"] = last_call

    developer_trace = state.get("developer_trace") if payload.developer_mode else None

    return EmailGenerateResponse(
        draft=draft,
        metadata={k: v for k, v in metadata.items() if v is not None},
        review_notes=review_notes,
        saved=saved,
        metrics=usage_summary,
        context_mode=context_mode,
        developer_trace=developer_trace,
    )
