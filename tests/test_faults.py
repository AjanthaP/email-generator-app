"""Day 2: each fault leaves its own telemetry signature, and faults stay local."""
import json
import os
import time
import types
from typing import Any, Dict, List

import pytest

from scripts.triage.scripted_llm import ScriptedGemini
from src.utils import faults
from src.utils.config import settings
from src.workflow.pipeline import execute_workflow

PROMPT = "Recipient: Priya\n\nLength preference: 90\n\nFollow up on the proposal we sent last week and ask for feedback."


@pytest.fixture
def env(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("FAULTS", raising=False)
    monkeypatch.setattr(settings, "enable_faults", True)
    monkeypatch.setattr(settings, "telemetry_sinks", "file")
    monkeypatch.setattr(settings, "telemetry_file", str(path))
    monkeypatch.setattr(settings, "enable_llm_router", False)
    monkeypatch.setattr(settings, "enable_chromadb", False, raising=False)
    # Skip the wrapper's retry back-off only; patching time.sleep itself would
    # also cancel the slow_model delay.
    monkeypatch.setattr("src.utils.llm_wrapper.time", types.SimpleNamespace(sleep=lambda s: None, time=time.time))
    return path


def run(spec: str = "", n: int = 1) -> None:
    for i in range(n):
        llm = None
        with (faults.injected(spec, seed=i) if spec else _null()):
            llm = ScriptedGemini(
                model=settings.gemini_model,
                max_output_tokens=faults.max_output_tokens() or settings.max_tokens,
                latency_ms=(1.0, 2.0),
                seed=i,
            )
            execute_workflow(PROMPT, llm=llm, use_stub=False, length_preference=90, endpoint="test")


class _null:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


def events(path) -> List[Dict[str, Any]]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def summaries(path) -> List[Dict[str, Any]]:
    return [e for e in events(path) if e["event"] == "request_summary"]


def test_healthy_baseline(env):
    run()
    s = summaries(env)[0]
    assert s["llm_calls"] == 6 and s["llm_errors"] == 0 and not s["is_fallback"]
    assert abs(s["length_deviation_pct"]) < 10


def test_quota_all_calls_falls_back_to_stub(env):
    run("quota_429:1.0")
    s = summaries(env)[0]
    assert s["source"] == "stub" and s["stub_reason"] == "quota_fallback"
    assert s["error_types"] == {"quota": 1} and s["retries"] == 3


def test_quota_partial_is_silent(env):
    run("quota_429:0.5", n=6)
    ss = summaries(env)
    assert sum(s["llm_errors"] for s in ss) > 0
    assert any(s["source"] == "llm" and s["is_fallback"] for s in ss), "some requests degrade without a stub"


def test_slow_model_hits_one_agent(env):
    run("slow_model:review:0.3")
    calls = [e for e in events(env) if e["event"] == "llm_call"]
    review = [c for c in calls if c["agent"] == "review"][0]
    others = [c for c in calls if c["agent"] != "review"]
    assert review["latency_ms"] >= 300 and max(c["latency_ms"] for c in others) < 300


def test_truncate(env):
    run("truncate:20")
    s = summaries(env)[0]
    assert s["truncated_calls"] >= 1 and s["finish_reasons"].get("MAX_TOKENS")
    assert "input_parser" in s["fallback_agents"]  # cut-off JSON can't be parsed


def test_bad_prompt_changes_length_without_errors(env):
    run("bad_prompt:3")
    s = summaries(env)[0]
    assert s["prompt_version"] == "v2" and s["llm_errors"] == 0 and not s["is_fallback"]
    assert s["length_deviation_pct"] > 100


def test_parser_garbage(env):
    run("parser_garbage")
    s = summaries(env)[0]
    assert s["fallback_agents"] == ["input_parser"] and s["llm_errors"] == 0


def test_agent_crash(env):
    run("agent_crash:tone_stylist")
    s = summaries(env)[0]
    assert s["agents_errored"] == ["tone_stylist"] and s["source"] == "llm"


def test_cost_spike(env, tmp_path):
    run()
    base = summaries(env)[0]["tokens_in"]
    run("cost_spike:5")
    spiked = summaries(env)[1]["tokens_in"]
    assert spiked > 3 * base


def test_no_fault_names_in_telemetry(env):
    for spec in ["quota_429:0.5", "slow_model:review:0.01", "truncate:20", "bad_prompt", "parser_garbage", "agent_crash", "cost_spike"]:
        run(spec)
    text = env.read_text(encoding="utf-8").lower()
    for word in ["fault", "inject", "scripted", "quota_429", "slow_model", "parser_garbage", "agent_crash", "cost_spike", "bad_prompt"]:
        assert word not in text, f"telemetry mentions {word!r}"


def test_off_unless_enabled(monkeypatch):
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setattr(settings, "enable_faults", False)
    assert not faults.enabled()
    with pytest.raises(RuntimeError):
        with faults.injected("quota_429"):
            pass
    assert faults.plan_call("review", {"target_length": 90}).params == {"target_length": 90}


def test_always_off_on_cloud_run(monkeypatch):
    monkeypatch.setattr(settings, "enable_faults", True)
    monkeypatch.setenv("K_SERVICE", "email-generator-app")
    monkeypatch.setenv("FAULTS", "quota_429")
    assert not faults.enabled() and faults.active() is None


def test_parse_rejects_bad_specs():
    assert faults.parse("slow_model:review:2")["slow_model"].args == ("review", 2.0)
    for bad in ["nope", "slow_model:nobody", "truncate:1:2"]:
        with pytest.raises(ValueError):
            faults.parse(bad)


def test_generator_smoke(tmp_path, monkeypatch):
    from scripts.triage import generate_incidents as gen

    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setattr("src.utils.llm_wrapper.time", types.SimpleNamespace(sleep=lambda s: None, time=time.time))
    monkeypatch.setattr(gen, "VARIANTS", {"agent_crash": ["agent_crash:review"], "bad_prompt": ["bad_prompt:3"]})
    out = tmp_path / "run"
    try:
        assert gen.main(["--out", str(out), "--per-fault", "1", "--healthy", "1", "--requests", "1", "--baseline", "1"]) == 0
    finally:
        os.environ.pop("K_REVISION", None)
        settings.telemetry_file = None
        settings.telemetry_sinks = "auto"
        settings.enable_faults = False
    labels = [json.loads(l) for l in (out / "incidents.jsonl").read_text().splitlines()]
    assert sorted(l["root_cause"] for l in labels) == ["agent_exception", "healthy", "prompt_regression"]
    assert not any(l["contaminated"] for l in labels)
    assert json.loads((out / "manifest.json").read_text())["windows"] == 3
