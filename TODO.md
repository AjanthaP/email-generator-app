# TODO: AI-Enabled Log Triage (4-Day Plan)

**Goal:** Build an AI agent that reads this app's telemetry and explains what broke, why, and which change caused it. Measure its accuracy on labelled incidents, then improve it and publish the numbers.

**Headline demo:** When Gemini runs out of quota, the app quietly falls back to the stub generator and still returns HTTP 200 (`src/workflow/pipeline.py`, `_is_quota_error`). Users get a template email and see no error. The triage agent should spot this from the telemetry alone: *"Stub fallback rate rose from 0% to 40% at 10:05. Root cause: Gemini quota exhaustion. Affected: all agents."*

**Definition of done:** a public repo with one command that runs the eval, a results table showing before → after accuracy, a 2-minute demo video, and a write-up.

---

## Day 0: Before starting (15 min)

- [x] **Revoke the Gemini API key** that was committed in `.env.minimal.railway`, and create a new one (Google AI Studio). It is still in git history, so rotating it is the only real fix. *Done: old key revoked, Cloud Run uses the new one.*
- [x] ~~**Generate a new `JWT_SECRET_KEY`**. The old one is in git history too.~~ *Not needed: the code never reads `JWT_SECRET_KEY`; sessions use random tokens.*
- [x] ~~If production auth uses the JSON users file, the old `admin@example.com` account has a publicly known password (`scripts/setup_auth.py`). Change it, or recreate the users with your own passwords.~~ *Not needed: the account is only created by running `scripts/setup_auth.py` by hand. The container never runs it and `data/users/` ships empty, so it doesn't exist in production.*
- [x] Merge the `chore/repo-cleanup` branch. *Done: PR #4.*

---

## Day 1: Instrument the pipeline

Most of this already exists: `src/utils/llm_wrapper.py` records model, latency, tokens, cost and errors for each LLM call. It's missing context and persistence.

- [ ] **Add fields to each call record** (`CallRecord` in `src/utils/metrics.py`): `request_id`, `agent`, `prompt_version`, `finish_reason`, `retries`, `is_fallback`.
- [ ] **Pass the agent name** into `LLMWrapper.invoke_chain(..., agent="draft_writer")` from each agent in `src/agents/`.
- [ ] **Generate a `request_id`** in `POST /api/email/generate` (`src/api/routers/email.py`). Pass it explicitly into `execute_workflow()`, and set a `contextvars` value *inside* the worker thread, because the workflow runs via `run_in_threadpool`.
- [ ] **Route the Router agent through the wrapper.** `src/agents/router.py` calls `self.llm.invoke(prompt)` directly, so its calls are never metered, and it runs on every request.
- [ ] **Save every call:** add an `llm_calls` table in `src/db/models.py` (Postgres), with JSONL in `data/metrics/` as the fallback when there's no `DATABASE_URL`. Today the metrics live in one in-memory list for the whole process and are lost on restart.
- [ ] **Add a per-request summary row**, `requests`, with: `request_id`, `source` (llm/stub), agents that errored or were skipped (from `review_notes`), length deviation vs. target (from the existing `original_word_count` / `final_word_count` metadata), total latency and total cost.
- [ ] **Add a version tag** for prompts: `PROMPT_VERSION = "v1"` in `src/utils/prompts.py`, logged on every call.
- [ ] **Switch logs to JSON lines** (one event per line) in `src/api/main.py` so the agent can query them.

**Done when:** one generation produces about 7 call rows that share one `request_id`, plus one summary row.

---

## Day 2: Fault injection and a labelled incident dataset

- [ ] **Create `src/utils/faults.py`**: fault switches read from env vars or a request header, active only when `ENABLE_FAULTS=true`.

  | Fault | How | What the telemetry shows |
  |---|---|---|
  | `quota_429` | Raise a ResourceExhausted-style error in the wrapper | Stub fallback, HTTP 200, no visible error |
  | `slow_model` | `sleep(N)` before the LLM call | p95 latency spike on one agent |
  | `truncate` | `max_output_tokens=20` | `finish_reason=MAX_TOKENS`, drafts cut off |
  | `bad_prompt` | Swap in a degraded prompt version | Length deviation jumps, **zero errors** |
  | `parser_garbage` | Input parser gets invalid JSON | Parser fallback warnings |
  | `agent_crash` | `tone_stylist` raises an exception | Agent silently skipped, email unstyled |
  | `cost_spike` | Pad the context 5× | Tokens and cost per request up 5× |

- [ ] **Create `scripts/triage/generate_incidents.py`**: run about 25 time windows of generations, each with 0 or 1 fault switched on. Write `data/triage/incidents.jsonl` with `{incident_id, window_start, window_end, fault, root_cause, affected_agent}`.
- [ ] **Include about 5 healthy windows** with no fault, where the agent should answer "healthy". This catches false alarms.

**Done when:** at least 20 labelled windows exist, with matching telemetry in the DB or JSONL.

---

## Day 3: Triage agent (MCP server) and eval

- [ ] **Create a new top-level `triage/` package**, kept separate from the app so it only reads telemetry and could point at any app.
- [ ] **Build an MCP server** (Python `mcp` SDK / FastMCP) with these tools:
  - `query_calls(start, end, agent=None, errors_only=False)`
  - `metrics_summary(start, end)`: p50/p95 latency, error rate, stub-fallback rate, cost per request and length deviation, broken down by agent
  - `get_trace(request_id)`: every call in one request, in order
  - `recent_changes(start, end)`: prompt-version, config and deploy events
- [ ] **Write the agent loop**: given an alert window, call the tools and return JSON: `{status, root_cause_category, affected_agent, evidence[], suggested_fix}`. Keep the model name configurable.
- [ ] **Write `triage/eval.py`**: run the agent on every labelled window and score `root_cause_category` and `affected_agent` against the labels. Print accuracy, a per-fault confusion table, and average cost and latency per diagnosis.
- [ ] **Record the baseline numbers** in `docs/triage/RESULTS.md`.

**Done when:** `python -m triage.eval` prints the accuracy table.

---

## Day 4: Improve, then ship

- [ ] **Morning, the improvement loop:** read the eval failures and fix the top 1–2 causes (a missing tool, a vague system prompt, a missing fallback-rate signal). Re-run the eval and record **before → after** in `RESULTS.md`. This number is the centrepiece of the write-up.
- [ ] **Add basic hardening:** a cap on tool calls per diagnosis, a timeout, and handling for the case where telemetry is empty.
- [ ] **Add a README section "AI log triage"** with an architecture diagram (`docs/diagrams/triage.mermaid`), the results table and how to run it.
- [ ] **Record a 2-minute demo:** switch on `quota_429`, show the app still returning 200 with stub emails, run triage, show the diagnosis.
- [ ] **Write a ~1,000-word post:** the problem (silent LLM failures), the design, the numbers, and what didn't work. Then a LinkedIn post linking the repo and video.
- [ ] **Add a resume bullet** with the final number, for example: *"Built an LLM incident-triage agent (MCP tools over pipeline telemetry): X% root-cause accuracy across 7 injected failure modes."*

---

## Later (out of scope for 4 days)

- [ ] OpenTelemetry traces exported to Grafana or CloudWatch
- [ ] An LLM-judge quality score per email, in addition to length deviation
- [ ] Model routing (a cheaper model for simple agents) with cost before/after
- [ ] Convert the remaining `print()` calls in `src/auth/oauth_providers.py`, `src/integrations/gmail_service.py`, `src/integrations/mcp_integration.py` and `src/context/chroma_context.py` to loggers
- [ ] Fix the 3 tests that already error at collection: `tests/test_agents_structure.py`, `tests/test_langsmith_config.py` and `tests/test_refinement_agent.py`. Also turn `tests/test_generate_with_tracing.py` and `tests/test_langsmith_trace.py` into real pytest tests (they're scripts today).
- [ ] Remove `|| true` from the CI test step in `.github/workflows/railway-deploy.yml` so failing tests block merges
- [ ] Review `scripts/legacy/` and delete what's no longer needed
