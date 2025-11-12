Enhancement: LLM Wrapper and Agent Integration

Goal
----
Add a lightweight LLM wrapper that centralizes retry/backoff and honors server-suggested retry delays. Then update agents to use the wrapper to reduce fallbacks and improve stability under transient errors or quota spikes.

What I added
------------
- `src/utils/llm_wrapper.py`: a synchronous LLM wrapper with:
  - `run_with_retries(func, ...)` — wrap any callable (e.g., `chain.invoke`) and retry on exceptions using exponential backoff.
  - `_parse_retry_delay(exc)` — heuristic to parse server-suggested retry delays from exception text (e.g., "Please retry in 51.6s" or `retry_delay { seconds: 51 }`).
  - `invoke_chain(chain, params)` — convenience to call a LangChain-like chain's `invoke` method with retries.

Why this helps
---------------
- Centralized retry logic avoids duplicating backoff behavior across agents.
- Honors server-suggested retry delays when available, reducing hammering the API.
- Keeps agents simple: they call wrapper.invoke_chain(...) instead of handling exceptions themselves.

How agents should be updated (examples)
--------------------------------------
Below are suggested edits for agents to adopt the wrapper. These are examples only — they are not applied to sources yet.

1) DraftWriterAgent example (before)

```python
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | self.llm
response = chain.invoke({
    "recipient": parsed_data.get("recipient_name", ""),
    "purpose": parsed_data.get("email_purpose", ""),
    "key_points": parsed_data.get("key_points", []),
    "tone": tone
})
```

(after — using `LLMWrapper` instance stored on the agent as `self.llm_wrapper`)

```python
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | self.llm
# use wrapper to call chain.invoke with retries/backoff
response = self.llm_wrapper.invoke_chain(chain, {
    "recipient": parsed_data.get("recipient_name", ""),
    "purpose": parsed_data.get("email_purpose", ""),
    "key_points": parsed_data.get("key_points", []),
    "tone": tone
})

# then use response.content as before
```

2) InputParserAgent example

Replace `response = chain.invoke({"user_input": user_input})` with:

```python
response = self.llm_wrapper.invoke_chain(chain, {"user_input": user_input})
```

3) ReviewAgent / Personalization / ToneStylist

Same pattern: call `self.llm_wrapper.invoke_chain(chain, params)` instead of `chain.invoke`.

How to wire the wrapper in `create_agents`
-------------------------------------------
Update `src/workflow/langgraph_flow.py` where agents are created. Instead of passing raw `ChatGoogleGenerativeAI` to each agent, create a `LLMWrapper` and pass that (and optionally the raw LLM if needed):

```python
from src.utils.llm_wrapper import LLMWrapper

llm = ChatGoogleGenerativeAI(...)
wrapper = LLMWrapper(llm, max_retries=3)

input_parser = InputParserAgent(llm=llm, llm_wrapper=wrapper)
intent_detector = IntentDetectorAgent(llm=llm, llm_wrapper=wrapper)
# ...
```

Agents can accept an optional `llm_wrapper` argument, defaulting to `make_wrapper(llm)` if not passed.

Fallback / metadata behavior
----------------------------
- Keep the existing stub fallback in `langgraph_flow.execute_workflow`. The wrapper increases the chance the real LLM will succeed by retrying transient errors and honoring delays.
- When a hard quota/429 is returned and not recoverable (or after exhausted retries), the wrapper will raise `LLMWrapperError`. The workflow's existing exception handling detects quota errors and falls back to the stub.

Next steps (recommended)
------------------------
1. Update agent `__init__` signatures to accept an optional `llm_wrapper` (default to `LLMWrapper(llm)` if not provided).
2. Replace `chain.invoke(...)` calls in agents with `self.llm_wrapper.invoke_chain(chain, params)`.
3. Optionally add a per-agent or per-call `max_retries` override when calling `invoke_chain` for fine-grained control.
4. Add unit tests that mock `chain.invoke` to raise a quota-like exception and assert the wrapper retries and ultimately raises `LLMWrapperError` after exhausting attempts.
5. Consider adding a small cache layer around the wrapper to reduce duplicate identical requests.

If you want I can apply the agent code changes now (non-risky substitutions) and run the test suite / lint. Let me know if you'd like me to proceed with applying the agent edits now or to stage them for a later commit.
