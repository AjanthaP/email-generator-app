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

- [x] **Add fields to each call record** (`CallRecord` in `src/utils/metrics.py`): `request_id`, `agent`, `prompt_version`, `finish_reason`, `retries`, `is_fallback`. *Done, plus `error_type` (quota / timeout / error). `is_fallback` lives in `agent_fallback` events and `request_summary.is_fallback` rather than on the call row: an agent decides to fall back after the call returns (for example, the parser gets a 200 with invalid JSON), so the call row can't know yet.*
- [x] **Pass the agent name** into `LLMWrapper.invoke_chain(..., agent="draft_writer")` from each agent in `src/agents/`.
- [x] **Generate a `request_id`** in `POST /api/email/generate` (`src/api/routers/email.py`). Pass it explicitly into `execute_workflow()`, and set a `contextvars` value *inside* the worker thread, because the workflow runs via `run_in_threadpool`. *Done. A safe client `X-Request-ID` is reused; the ID is returned in the `X-Request-ID` header and `metadata.request_id`. `/regenerate`, the extension and MCP paths get request IDs too.*
- [x] **Route the Router agent through the wrapper.** `src/agents/router.py` calls `self.llm.invoke(prompt)` directly, so its calls are never metered, and it runs on every request. *Done, with one attempt (no retries). Found while testing: `ROUTER_AGENT_PROMPT` had unescaped `{...}` braces, so formatting it always raised and the router never actually called Gemini. Fixed the prompt and set `ENABLE_LLM_ROUTER` to `false` by default, which keeps production behaving as it did. Setting it to `true` adds one Gemini call per request. The pipeline doesn't act on its decision yet; see "Make the LLM router useful" under Later.*
- [x] ~~**Save every call:** add an `llm_calls` table in `src/db/models.py` (Postgres), with JSONL in `data/metrics/` as the fallback when there's no `DATABASE_URL`. Today the metrics live in one in-memory list for the whole process and are lost on restart.~~ *Decision (Nov 12): no database for now. Every event is one JSON line on stdout, which Cloud Run sends to Cloud Logging (30 days, SQL via Log Analytics), plus an append-only JSONL file locally (`data/metrics/events-YYYY-MM-DD.jsonl`). `TELEMETRY_SINKS=auto` turns the file off on Cloud Run, where disk is in memory. The Day 3 tools read through a store interface, so Firestore, BigQuery or Postgres can be added later as another backend. The in-memory list is now capped at 2,000 calls.*
- [x] **Add a per-request summary row**, `requests`, with: `request_id`, `source` (llm/stub), agents that errored or were skipped (from `review_notes`), length deviation vs. target (from the existing `original_word_count` / `final_word_count` metadata), total latency and total cost. *Done as the `request_summary` event. Deviation uses the pre-trim word count, because trimming would hide a prompt that writes far too much. Also records retries, finish reasons, truncated calls, tokens, and LLM latency next to wall-clock latency.*
- [x] **Add a version tag** for prompts: `PROMPT_VERSION = "v1"` in `src/utils/prompts.py`, logged on every call.
- [x] **Switch logs to JSON lines** (one event per line) in `src/api/main.py` so the agent can query them. *Done in `src/utils/logging_config.py`, uvicorn logs included. Every line carries `request_id` and `agent`. `LOG_FORMAT=text` for local reading. A `startup` event records revision, model and prompt version.*

**Done when:** one generation produces about 7 call rows that share one `request_id`, plus one summary row. *Verified in `tests/test_telemetry.py`: 7 rows with `ENABLE_LLM_ROUTER=true`, 6 with the default. Event schema: see the docstring of `src/utils/telemetry.py`.*

**Found on Day 1, to keep in mind:**
- The wrapper retries every error, quota included, and honours Gemini's "retry in Ns" hint (capped at 60 s). One exhausted-quota call can wait about 3 minutes before the stub fallback. Design the `quota_429` fault with this in mind.
- `ENABLE_CHROMADB` defaults to `true`. With the current ChromaDB version, setup fails, and it is retried on every personalization call (about 2 s each locally). Set `ENABLE_CHROMADB=false` for the Day 2 runs, and check whether Cloud Run sets it.

---

## Day 2: Fault injection and a labelled incident dataset

- [x] **Create `src/utils/faults.py`**: fault switches read from env vars or a request header, active only when `ENABLE_FAULTS=true`. *Done. Always off on Cloud Run (`K_SERVICE` set), whatever `ENABLE_FAULTS` says. Switch on with `FAULTS=...`, the `X-Fault` header on `/api/email/generate`, or `faults.injected(...)` in code. Spec: `name[:arg[:arg]]`, comma-separated, e.g. `quota_429:0.4` or `slow_model:review:2.5`. Injected errors look real and the module never logs, so the telemetry never names a fault (a test checks this).*

  | Fault | How | What the telemetry shows |
  |---|---|---|
  | `quota_429` | Raise a ResourceExhausted-style error in the wrapper | Stub fallback, HTTP 200, no visible error |
  | `slow_model` | `sleep(N)` before the LLM call | p95 latency spike on one agent |
  | `truncate` | `max_output_tokens=20` | `finish_reason=MAX_TOKENS`, drafts cut off |
  | `bad_prompt` | Swap in a degraded prompt version | Length deviation jumps, **zero errors** |
  | `parser_garbage` | Input parser gets invalid JSON | Parser fallback warnings |
  | `agent_crash` | `tone_stylist` raises an exception | Agent silently skipped, email unstyled |
  | `cost_spike` | Pad the context 5× | Tokens and cost per request up 5× |

  *As built: `quota_429:rate` fails each call with that probability, retries included (3 retries with a 1 s "retry in" hint). Only an input-parser failure gives the stub; later failures are swallowed by the agents, so most quota requests still say `source=llm`. `slow_model:agent:secs`. `truncate:max_tokens`. `bad_prompt:factor` asks Review for factor × the target length and reports `prompt_version=v2`. `agent_crash:agent` (default `tone_stylist`) raises an `AttributeError` before the agent runs. `cost_spike:factor` adds factor × 1,500 characters of earlier-thread context to every prompt (about 5× tokens at factor 5): repeating the template inputs alone only gave about 1.5×.*

- [x] **Create `scripts/triage/generate_incidents.py`**: run about 25 time windows of generations, each with 0 or 1 fault switched on. Write `data/triage/incidents.jsonl` with `{incident_id, window_start, window_end, fault, root_cause, affected_agent}`. *Done: 26 windows (3 variants of each of the 7 faults, plus 5 healthy). Each window has 4 requests, preceded by a 2-request healthy baseline (`baseline_start/end` in the label). Output goes to `data/triage/<scripted|live>/` (`telemetry.jsonl`, `incidents.jsonl`, `manifest.json`). Root-cause labels live in `triage/taxonomy.py`, shared with Day 3. Config-style faults (truncate, bad_prompt, agent_crash, cost_spike) come with a simulated deploy (a `startup` event with a new revision) and a rollback; 2 healthy windows get a harmless deploy too, so "a deploy happened" isn't the answer by itself. Labels whose healthy periods show errors are flagged `contaminated`.*
- [x] **Include about 5 healthy windows** with no fault, where the agent should answer "healthy". This catches false alarms.
- [x] **Model choice:** a scripted stand-in for Gemini (`scripts/triage/scripted_llm.py`) by default: free, offline, repeatable (`--seed`). It answers every agent's prompt in the right shape, writes emails of the requested length, counts tokens from the real text, and truncates at the token cap. Final numbers should come from `--live` (real Gemini), run on your PC:

  ```powershell
  python scripts\triage\generate_incidents.py --live     # needs GEMINI_API_KEY in .env; 156 requests, roughly 20-40 min with the default --pace 3, well under $1
  ```

  The scripted run takes about 3 minutes. The committed dataset is `data/triage/scripted/` (seed 7, 1,101 events, no contaminated windows).

**Done when:** at least 20 labelled windows exist, with matching telemetry in the DB or JSONL. *Done: 26 windows in `data/triage/scripted/`. Tests: `tests/test_faults.py` (14).*

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

- [ ] Cache the ChromaDB setup failure, or default `ENABLE_CHROMADB` to `false` (see Day 1 notes)
- [ ] `LLMWrapper.invoke_chain` logs a 200-character preview of every model response at INFO, so generated email text ends up in Cloud Logging. Consider DEBUG.
- [ ] **Make the LLM router useful, then decide whether to turn on `ENABLE_LLM_ROUTER`.** Day 1 fixed the prompt, metering and metadata merge, so the call now works (tested with a fake model only). Still missing:
  - [ ] **Act on `retry`.** Nothing reads `routing_decision` today, so `retry` does nothing and `fallback` (which replaces the draft with a template) is the only decision with an effect. Add a loop in `src/workflow/pipeline.py`: on `retry`, run Review again with the issues as feedback, add 1 to `retry_count`, and ask the router again.
  - [ ] **Cap retries with a setting, `ROUTER_MAX_RETRIES`, default `2`.** It replaces the hard-coded `max_retries=3` in `RouterAgent.__init__` and applies to both the LLM and the fixed-rules path.
  - [ ] **Tighten `route_next_step()`.** It returns `retry` for any Review issue (for example "Email too short"), so once the loop exists most requests would retry. Retry only on issues a Review pass can fix.
  - [ ] **Give it real inputs.** Its summary uses `error`, `retry_count` and `needs_improvement`, which the pipeline never sets. Use Review's issues, agent errors from `review_notes`, the agents that fell back (telemetry), and the length deviation.
  - [ ] **Guard `fallback`.** Replace the draft with the template only when it's unusable (empty, or no greeting); otherwise treat it as `continue`.
  - [ ] **Check against real Gemini.** Run some requests locally with `ENABLE_LLM_ROUTER=true`, then look at the router's `llm_call` events and how often it records `invalid_output` fallbacks.
  - Cost: one more Gemini call per request, plus one or more per retry (at most 2 retries).
  - Also useful for triage: a working retry loop adds a realistic failure mode, "retries quietly double the cost per request".

- [ ] OpenTelemetry traces exported to Grafana or CloudWatch
- [ ] An LLM-judge quality score per email, in addition to length deviation
- [ ] Model routing (a cheaper model for simple agents) with cost before/after
- [ ] Convert the remaining `print()` calls in `src/auth/oauth_providers.py`, `src/integrations/gmail_service.py`, `src/integrations/mcp_integration.py` and `src/context/chroma_context.py` to loggers
- [ ] Fix the 3 tests that already error at collection: `tests/test_agents_structure.py`, `tests/test_langsmith_config.py` and `tests/test_refinement_agent.py`. Also turn `tests/test_generate_with_tracing.py` and `tests/test_langsmith_trace.py` into real pytest tests (they're scripts today).
- [ ] Remove `|| true` from the CI test step in `.github/workflows/railway-deploy.yml` so failing tests block merges
- [ ] Review `scripts/legacy/` and delete what's no longer needed
