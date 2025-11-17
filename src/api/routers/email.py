"""Email generation endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.memory.memory_manager import MemoryManager
from src.utils.metrics import metrics
from src.workflow.langgraph_flow import execute_workflow, _init_llm
from src.agents.review import ReviewAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.utils.llm_wrapper import make_wrapper
from ..schemas import EmailGenerateRequest, EmailGenerateResponse, RegenerateRequest, RegenerateResponse

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
            length_preference=payload.length_preference,
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
            "requested_length_preference": payload.length_preference,
        }
    )

    # If trimming occurred in workflow metadata, reflect final word count here
    if "final_word_count" in metadata:
        metadata["final_word_count"] = metadata["final_word_count"]
        metadata["original_word_count"] = metadata.get("original_word_count")

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


def calculate_diff_ratio(original: str, edited: str) -> float:
    """Calculate percentage of content changed between original and edited drafts."""
    orig_words = set(original.lower().split())
    edit_words = set(edited.lower().split())
    
    if not orig_words and not edit_words:
        return 0.0
    
    # Symmetric difference (words added or removed)
    diff_words = orig_words ^ edit_words
    total_words = max(len(orig_words), len(edit_words))
    
    return len(diff_words) / total_words if total_words > 0 else 0.0


@router.post("/regenerate", response_model=RegenerateResponse)
async def regenerate_draft(payload: RegenerateRequest) -> RegenerateResponse:
    """
    Regenerate draft from user-edited version using adaptive workflow.
    
    Decision logic:
    - If < 20% changed: Run ReviewAgent only (fast, 1 LLM call)
    - If >= 20% changed: Run ToneStylist → PersonalizationAgent → ReviewAgent (full polish)
    """
    if not payload.edited_draft.strip():
        raise HTTPException(status_code=400, detail="Edited draft must not be empty")
    
    try:
        # Calculate diff ratio
        diff_ratio = calculate_diff_ratio(payload.original_draft, payload.edited_draft)
        
        # Initialize LLM and wrapper
        llm = _init_llm()
        wrapper = make_wrapper(llm)
        
        # Determine workflow type (20% threshold)
        use_full_workflow = payload.force_full_workflow or diff_ratio >= 0.20
        workflow_type = "full" if use_full_workflow else "lightweight"
        
        if use_full_workflow:
            # Major edits: Full re-polish pipeline
            # Step 1: Tone adjustment
            tone_stylist = ToneStylistAgent(llm, llm_wrapper=wrapper)
            styled_draft = await run_in_threadpool(
                tone_stylist.adjust_tone,
                payload.edited_draft,
                payload.tone,
                payload.length_preference or 170
            )
            
            # Step 2: Personalization
            personalizer = PersonalizationAgent(llm, llm_wrapper=wrapper)
            personalization_state = {
                "draft": styled_draft,
                "user_id": payload.user_id,
                "length_preference": payload.length_preference
            }
            personalized_result = await run_in_threadpool(
                personalizer,
                personalization_state
            )
            personalized_draft = personalized_result.get("personalized_draft", styled_draft)
            
            # Step 3: Review + refinement
            reviewer = ReviewAgent(llm, llm_wrapper=wrapper)
            review_state = {
                "personalized_draft": personalized_draft,
                "tone": payload.tone,
                "intent": payload.intent,
                "length_preference": payload.length_preference
            }
            final_result = await run_in_threadpool(reviewer, review_state)
            final_draft = final_result.get("final_draft", personalized_draft)
            metadata = final_result.get("metadata", {})
            
        else:
            # Minor edits: Lightweight review only
            reviewer = ReviewAgent(llm, llm_wrapper=wrapper)
            review_state = {
                "personalized_draft": payload.edited_draft,
                "tone": payload.tone,
                "intent": payload.intent,
                "length_preference": payload.length_preference
            }
            final_result = await run_in_threadpool(reviewer, review_state)
            final_draft = final_result.get("final_draft", payload.edited_draft)
            metadata = final_result.get("metadata", {})
        
        # Collect metrics
        usage_summary = metrics.session_summary()
        
        return RegenerateResponse(
            final_draft=final_draft,
            workflow_type=workflow_type,
            diff_ratio=round(diff_ratio, 3),
            metadata={
                **metadata,
                "diff_threshold": 0.20,
                "original_length": len(payload.original_draft.split()),
                "edited_length": len(payload.edited_draft.split()),
                "final_length": len(final_draft.split())
            },
            metrics=usage_summary
        )
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {exc}") from exc
