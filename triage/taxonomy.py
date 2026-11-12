"""Root-cause labels shared by the incident generator, the triage agent and the eval.

This package only reads telemetry; it does not import the app.
"""

ROOT_CAUSES = {
    "healthy": "No incident: telemetry is within its normal range",
    "quota_exhausted": "LLM provider quota or rate-limit (429) errors",
    "model_latency": "One agent's LLM calls became slow",
    "output_truncation": "Model replies cut off at the output-token limit",
    "prompt_regression": "A prompt change degraded output (for example, length) without errors",
    "malformed_output": "The model returned output an agent could not parse",
    "agent_exception": "An agent raised an exception and was skipped",
    "cost_regression": "Tokens and cost per request rose sharply",
}

AGENTS = (
    "input_parser", "intent_detector", "draft_writer", "tone_stylist",
    "personalization", "review", "router",
)
ALL_AGENTS = "all"

# Fault switch (src/utils/faults.py) -> root cause label.
FAULT_TO_ROOT_CAUSE = {
    None: "healthy",
    "quota_429": "quota_exhausted",
    "slow_model": "model_latency",
    "truncate": "output_truncation",
    "bad_prompt": "prompt_regression",
    "parser_garbage": "malformed_output",
    "agent_crash": "agent_exception",
    "cost_spike": "cost_regression",
}
