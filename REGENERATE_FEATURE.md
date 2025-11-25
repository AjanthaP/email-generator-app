# Adaptive Regenerate Feature

## Overview
The regenerate feature allows users to edit generated email drafts and intelligently re-process them. The system automatically selects between lightweight and full workflow based on edit magnitude, optimizing quota usage.

## Architecture

### Workflow Selection Logic
- **Diff Calculation**: Word-level symmetric difference between original and edited drafts
- **Threshold**: 20% changed content
- **Lightweight Path** (< 20% changes): ReviewAgent only (1 LLM call)
  - Use case: Minor grammar fixes, small tweaks, formatting adjustments
- **Full Path** (≥ 20% changes): ToneStylist → PersonalizationAgent → ReviewAgent (3 LLM calls)
  - Use case: Major content rewrites, tone shifts, substantial additions/deletions

### Backend Implementation

**Endpoint**: `POST /api/email/regenerate`

**Request Schema** (`RegenerateRequest`):
```python
{
    "original_draft": str,         # Initial generated draft
    "edited_draft": str,           # User-edited version
    "tone": str,                   # Desired tone (formal/casual/friendly/persuasive)
    "intent": str,                 # Email intent (outreach/followup/meeting/etc.)
    "recipient": Optional[str],    # Recipient context
    "length_preference": str,      # short/medium/long
    "user_id": str,
    "force_full_workflow": bool    # Override diff-based routing (default: False)
}
```

**Response Schema** (`RegenerateResponse`):
```python
{
    "final_draft": str,             # Regenerated email
    "workflow_type": str,           # "lightweight" | "full"
    "diff_ratio": float,            # 0.0-1.0 (percentage of words changed)
    "metadata": dict,               # Agent metadata
    "metrics": dict,                # Performance metrics (execution_time_ms)
}
```

**Diff Calculation** (`calculate_diff_ratio`):
```python
def calculate_diff_ratio(original: str, edited: str) -> float:
    """
    Calculates symmetric word-level difference ratio.
    
    Formula: (words_only_in_original + words_only_in_edited) / total_unique_words
    Returns: 0.0 (identical) to 1.0 (completely different)
    """
    original_words = set(original.lower().split())
    edited_words = set(edited.lower().split())
    
    symmetric_diff = original_words.symmetric_difference(edited_words)
    total_unique = original_words.union(edited_words)
    
    return len(symmetric_diff) / len(total_unique) if total_unique else 0.0
```

**Adaptive Routing**:
```python
@router.post("/regenerate")
async def regenerate_draft(payload: RegenerateRequest):
    start_time = time.time()
    
    # Calculate diff ratio
    diff_ratio = calculate_diff_ratio(payload.original_draft, payload.edited_draft)
    
    # Route workflow
    if payload.force_full_workflow or diff_ratio >= 0.20:
        # Major edits: Full workflow
        workflow_type = "full"
        
        # Step 1: Tone styling
        tone_result = await tone_stylist.apply_tone(...)
        
        # Step 2: Personalization
        personalized_result = await personalization_agent.personalize(...)
        
        # Step 3: Review & refinement
        final_result = await review_agent.review(...)
    else:
        # Minor edits: Lightweight workflow
        workflow_type = "lightweight"
        
        # Single-pass review only
        final_result = await review_agent.review(...)
    
    execution_time_ms = (time.time() - start_time) * 1000
    
    return RegenerateResponse(
        final_draft=final_result.refined_draft,
        workflow_type=workflow_type,
        diff_ratio=diff_ratio,
        metadata=final_result.metadata,
        metrics={"execution_time_ms": execution_time_ms}
    )
```

### Frontend Implementation

**State Management** (`App.tsx`):
```tsx
const [originalDraft, setOriginalDraft] = useState('')        // Baseline for diff
const [isEdited, setIsEdited] = useState(false)               // Track if user edited
const [isRegenerating, setIsRegenerating] = useState(false)   // Loading state
const [regenerateInfo, setRegenerateInfo] = useState<{        // Last regenerate details
  workflowType: string;
  diffRatio: number;
} | null>(null)
```

**Edit Tracking**:
```tsx
function handleDraftChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
  const newValue = event.target.value
  setDraftText(newValue)
  setIsEdited(newValue !== originalDraft)  // Auto-detect edits
}
```

**Regenerate Handler**:
```tsx
async function handleRegenerate() {
  if (!isEdited || !originalDraft || !result) return

  setIsRegenerating(true)
  setError(null)
  try {
    const response = await regenerateDraft({
      original_draft: originalDraft,
      edited_draft: draftText,
      tone: result.metadata.tone as string || tone,
      intent: result.metadata.intent as string || 'outreach',
      recipient: recipient || undefined,
      length_preference: lengthPreference,
      user_id: normalizedUserId,
    })

    // Update UI with regenerated draft
    setDraftText(response.final_draft)
    setOriginalDraft(response.final_draft)  // New baseline
    setIsEdited(false)
    setRegenerateInfo({
      workflowType: response.workflow_type,
      diffRatio: response.diff_ratio,
    })
    
    setCopyStatus(
      `Regenerated using ${response.workflow_type} workflow (${(response.diff_ratio * 100).toFixed(0)}% changed)`
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Regeneration failed.'
    setError(message)
  } finally {
    setIsRegenerating(false)
  }
}
```

**UI Components**:
```tsx
{/* Textarea with edit tracking */}
<textarea
  className="draft__content"
  value={draftText}
  onChange={handleDraftChange}  // Tracks edits automatically
  rows={16}
/>

{/* Action buttons */}
<div className="draft__actions">
  <button onClick={handleCopyDraft}>Copy Draft</button>
  
  <button 
    onClick={handleRegenerate} 
    disabled={isRegenerating || !isEdited}  // Only enable when edited
  >
    {isRegenerating ? 'Regenerating…' : 'Regenerate Draft'}
  </button>
  
  {/* Workflow type badge */}
  {regenerateInfo && (
    <span className="regenerate-badge">
      {regenerateInfo.workflowType === 'lightweight' ? '⚡ Quick polish' : '🔄 Full re-polish'}
      {' '}({(regenerateInfo.diffRatio * 100).toFixed(0)}% changed)
    </span>
  )}
</div>
```

## Quota Optimization

### LLM Call Comparison
| Scenario | Old Approach | New Approach | Savings |
|----------|-------------|--------------|---------|
| Minor edit (5% changed) | 3 calls (full pipeline) | 1 call (review only) | **67% reduction** |
| Medium edit (15% changed) | 3 calls (full pipeline) | 1 call (review only) | **67% reduction** |
| Major edit (25% changed) | 3 calls (full pipeline) | 3 calls (full pipeline) | No change |
| Major rewrite (50% changed) | 3 calls (full pipeline) | 3 calls (full pipeline) | No change |

### Expected Usage Pattern
Assuming typical user behavior:
- 70% of regenerations are minor tweaks (grammar, small additions) → Lightweight path
- 30% of regenerations are major rewrites → Full path

**Average quota savings**: `0.70 × 67% + 0.30 × 0% = 46.9% reduction in regenerate LLM calls`

## User Experience

### Transparency Features
1. **Edit Detection**: Button disabled until user makes changes
2. **Workflow Feedback**: Badge shows which workflow was used
3. **Diff Percentage**: Shows magnitude of changes made
4. **Status Messages**: Copy status shows workflow type and percentage

### Example Workflow
1. User generates email: "Dear John, I hope this email finds you well..."
2. User edits: Changes "I hope this email finds you well" → "Hope you're doing great"
3. User clicks "Regenerate Draft"
4. System calculates: ~8% changed (4 words different out of 50)
5. System routes to: Lightweight workflow (ReviewAgent only)
6. UI shows: "⚡ Quick polish (8% changed)"
7. Result: Grammar checked, tone verified, ready in ~2 seconds

### Edge Cases Handled
- **Empty edits**: Button stays disabled if `draftText === originalDraft`
- **Whitespace-only changes**: Diff calculation ignores whitespace differences
- **Full rewrites**: Automatically routes to full workflow for comprehensive re-processing
- **Force full workflow**: Optional parameter to always use full pipeline (future enhancement)

## Testing Recommendations

### Unit Tests
```python
# test_regenerate_endpoint.py
def test_diff_calculation_identical():
    assert calculate_diff_ratio("hello world", "hello world") == 0.0

def test_diff_calculation_partial():
    assert 0.0 < calculate_diff_ratio("hello world", "hello there") < 1.0

def test_diff_calculation_completely_different():
    assert calculate_diff_ratio("hello world", "goodbye universe") > 0.5

def test_lightweight_workflow_routing():
    # 10% changed → should use lightweight
    payload = RegenerateRequest(
        original_draft="A" * 100,
        edited_draft="A" * 90 + "B" * 10,  # 10% different
        ...
    )
    response = await regenerate_draft(payload)
    assert response.workflow_type == "lightweight"

def test_full_workflow_routing():
    # 30% changed → should use full
    payload = RegenerateRequest(
        original_draft="A" * 100,
        edited_draft="A" * 70 + "B" * 30,  # 30% different
        ...
    )
    response = await regenerate_draft(payload)
    assert response.workflow_type == "full"
```

### Integration Tests
- Test regenerate with real draft samples
- Verify ToneStylist → Personalization → Review chain works
- Verify ReviewAgent standalone works
- Test force_full_workflow override
- Test quota usage tracking (count LLM calls)

### Manual Testing Scenarios
1. **Minor grammar fix**: Change "there" → "their", expect lightweight
2. **Add salutation**: Add "Hi [Name]," to start, expect lightweight
3. **Change tone completely**: Formal → Casual throughout, expect full
4. **Rewrite half**: Replace 50%+ content, expect full
5. **Whitespace only**: Add line breaks, expect lightweight (no content change)

## Future Enhancements

### Configuration
- Make diff threshold configurable via `settings.regenerate_diff_threshold`
- Allow per-user thresholds based on history

### Advanced Features
- **Smart diff**: Use semantic similarity instead of word-level diff
- **Incremental processing**: Only re-process changed paragraphs
- **Workflow explanation**: Show why lightweight vs full was chosen
- **Undo regenerate**: Restore previous version

### Analytics
- Track workflow type distribution (lightweight vs full usage)
- Measure quota savings vs. old approach
- User satisfaction by workflow type

## Files Modified

### Backend
- `src/api/schemas.py`: Added `RegenerateRequest`, `RegenerateResponse`
- `src/api/routers/email.py`: Added `calculate_diff_ratio()`, `regenerate_draft()` endpoint

### Frontend
- `frontend/src/lib/api.ts`: Added `regenerateDraft()` function, TypeScript interfaces
- `frontend/src/App.tsx`: Added state, `handleRegenerate()`, `handleDraftChange()`, UI components

## Deployment Notes

### Environment Variables
No new environment variables required. Uses existing:
- `GEMINI_API_KEY`: For LLM calls
- `VITE_API_BASE_URL`: Frontend API endpoint

### Database
No schema changes required. Regenerated drafts can be saved to history using existing flow.

### Monitoring
Recommended metrics to track:
- `regenerate_workflow_type_distribution` (lightweight vs full ratio)
- `regenerate_avg_diff_ratio` (average edit magnitude)
- `regenerate_response_time_by_workflow` (performance comparison)
- `regenerate_quota_savings` (cumulative LLM calls saved)

## Status

✅ **Backend**: Fully implemented and deployed
✅ **Frontend**: Fully implemented
⏳ **Testing**: Pending quota reset (429 errors currently)
📋 **Documentation**: Complete

---

**Last Updated**: Current conversation
**Implementation Phase**: Complete - Ready for testing
