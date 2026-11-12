"""Generate labelled incident windows for the triage eval.

Runs the real pipeline in-process through a sequence of time windows. Each
window has at most one fault switched on (``src/utils/faults.py``); healthy
windows have none. Every window is preceded by a short healthy baseline, so
the triage agent can compare "before" and "during". Output, in ``--out``:

- ``telemetry.jsonl``: every telemetry event of the run (what the agent reads)
- ``incidents.jsonl``: one label per window (what the eval scores against)
- ``manifest.json``: how the run was made

Usage (from the repo root)::

    python scripts/triage/generate_incidents.py            # scripted model, offline, ~3 min
    python scripts/triage/generate_incidents.py --live     # real Gemini; needs GEMINI_API_KEY

Labels never reach the telemetry: injected errors look real and nothing logs
a fault name. Config-style faults (truncate, bad_prompt, agent_crash,
cost_spike) arrive with a simulated deploy (a ``startup`` event with a new
revision) and are rolled back after the window; two healthy windows get a
harmless deploy too, so a deploy alone doesn't give the answer away.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import string
import subprocess
import sys
import time
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from triage.taxonomy import ALL_AGENTS, FAULT_TO_ROOT_CAUSE  # noqa: E402

# Three variants per fault, so the eval isn't scored on one exact signature.
VARIANTS: Dict[str, List[str]] = {
    "quota_429": ["quota_429:0.4", "quota_429:0.7", "quota_429:1.0"],
    "slow_model": ["slow_model:draft_writer:3", "slow_model:review:2.5", "slow_model:personalization:4"],
    "truncate": ["truncate:20", "truncate:40", "truncate:60"],
    "bad_prompt": ["bad_prompt:2.5", "bad_prompt:3", "bad_prompt:4"],
    "parser_garbage": ["parser_garbage", "parser_garbage", "parser_garbage"],
    "agent_crash": ["agent_crash:tone_stylist", "agent_crash:personalization", "agent_crash:review"],
    "cost_spike": ["cost_spike:4", "cost_spike:5", "cost_spike:6"],
}
DEPLOY_FAULTS = {"truncate", "bad_prompt", "agent_crash", "cost_spike"}
GAP_S = 0.02  # pause between baseline, window and rollback

# (recipient, request, tone)
PROMPTS = [
    ("Priya", "Follow up on the proposal we sent last week and ask whether she has feedback before Friday.", "formal"),
    ("Arjun", "Thank him for presenting at yesterday's team meeting and mention the customer examples he shared.", "casual"),
    ("Dr. Mehta", "Request a 30 minute meeting next week to review the Q3 roadmap.", "formal"),
    ("Sarah", "Apologise for missing the design review deadline and propose a new date.", "empathetic"),
    ("the leadership team", "Send a status update on the migration: 80% done, one blocker on database access.", "formal"),
    ("Ravi", "Ask for the API documentation and test credentials for the payments sandbox.", "formal"),
    ("Meera", "Introduce myself as the new engineering lead and suggest a quick call.", "casual"),
    ("my manager", "Request two days of leave next Thursday and Friday for a family function.", "formal"),
]
LENGTHS = [60, 90, 120, 150]


@dataclass
class Window:
    fault: Optional[str]
    spec: Optional[str]
    deploy: bool


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def affected_agent(fault: Optional[str], spec: Optional[str]) -> Optional[str]:
    if fault is None:
        return None
    if fault in ("slow_model", "agent_crash"):
        return spec.split(":")[1]
    if fault == "bad_prompt":
        return "review"
    if fault == "parser_garbage":
        return "input_parser"
    return ALL_AGENTS


def plan_windows(rng: random.Random, per_fault: int, healthy: int) -> List[Window]:
    windows = [Window(None, None, deploy=i < 2) for i in range(healthy)]
    for fault, variants in VARIANTS.items():
        for i in range(per_fault):
            windows.append(Window(fault, variants[i % len(variants)], deploy=fault in DEPLOY_FAULTS))
    rng.shuffle(windows)
    return windows


class Runner:
    def __init__(self, args: argparse.Namespace):
        from src.utils.config import settings

        self.args = args
        self.settings = settings
        self.rng = random.Random(args.seed)
        self.revision_n = 40 + self.rng.randint(0, 20)
        self.requests_ok = 0
        self.requests_failed = 0

    # ---- Deploys -----------------------------------------------------------
    def _new_revision(self) -> str:
        self.revision_n += 1
        suffix = "".join(self.rng.choice(string.ascii_lowercase) for _ in range(3))
        os.environ["K_REVISION"] = f"email-generator-app-{self.revision_n:05d}-{suffix}"
        return os.environ["K_REVISION"]

    def deploy(self, **overrides: Any) -> None:
        from src.utils import telemetry

        self._new_revision()
        telemetry.emit_startup(**overrides)

    # ---- Requests ------------------------------------------------------------
    def _make_llm(self):
        if self.args.live:
            return None  # the pipeline builds a real Gemini client (and applies `truncate`)
        from scripts.triage.scripted_llm import ScriptedGemini
        from src.utils import faults

        return ScriptedGemini(
            model=self.settings.gemini_model,
            max_output_tokens=faults.max_output_tokens() or self.settings.max_tokens,
            seed=self.rng.randint(0, 10**9),
        )

    def run_requests(self, n: int) -> None:
        from src.workflow.pipeline import execute_workflow

        for _ in range(n):
            recipient, request, tone = self.rng.choice(PROMPTS)
            length = self.rng.choice(LENGTHS)
            prompt = f"Recipient: {recipient}\n\nLength preference: {length}\n\n{request}"
            try:
                execute_workflow(
                    prompt, llm=self._make_llm(), use_stub=False, user_id="default",
                    tone=tone, length_preference=length, endpoint="email.generate",
                )
                self.requests_ok += 1
            except Exception as exc:  # the request summary records it too
                self.requests_failed += 1
                print(f"    request failed: {type(exc).__name__}: {str(exc)[:120]}")
            if self.args.pace:
                time.sleep(self.args.pace)

    def window(self, idx: int, w: Window) -> Dict[str, Any]:
        from src.utils import faults

        baseline_start = iso_now()
        self.run_requests(self.args.baseline)
        baseline_end = iso_now()
        time.sleep(GAP_S)  # no event may fall in two periods

        start = iso_now()
        if w.deploy:
            changes: Dict[str, Any] = {}
            if w.fault == "truncate":
                changes["max_tokens"] = int(w.spec.split(":")[1])
            if w.fault == "bad_prompt":
                changes["prompt_version"] = faults.BAD_PROMPT_VERSION
            self.deploy(**changes)
        ctx = faults.injected(w.spec, seed=self.args.seed * 1000 + idx) if w.spec else nullcontext()
        with ctx:
            self.run_requests(self.args.requests)
        end = iso_now()
        time.sleep(GAP_S)
        if w.deploy and w.fault:
            self.deploy()  # roll back

        return {
            "incident_id": f"inc-{idx + 1:03d}",
            "window_start": start,
            "window_end": end,
            "baseline_start": baseline_start,
            "baseline_end": baseline_end,
            "fault": w.fault,
            "fault_spec": w.spec,
            "root_cause": FAULT_TO_ROOT_CAUSE[w.fault],
            "affected_agent": affected_agent(w.fault, w.spec),
            "requests": self.args.requests,
            "deploy": w.deploy,
        }


def summarize(events: List[Dict[str, Any]], start: str, end: str) -> Dict[str, Any]:
    in_win = [e for e in events if start <= e["ts"] <= end]
    reqs = [e for e in in_win if e["event"] == "request_summary"]
    calls = [e for e in in_win if e["event"] == "llm_call"]
    lat = sorted(e["latency_ms"] for e in reqs) or [0.0]
    devs = [abs(e["length_deviation_pct"]) for e in reqs if e.get("length_deviation_pct") is not None]
    return {
        "requests": len(reqs),
        "fallback_rate": round(sum(1 for e in reqs if e["is_fallback"]) / len(reqs), 2) if reqs else 0.0,
        "stub_rate": round(sum(1 for e in reqs if e["source"] == "stub") / len(reqs), 2) if reqs else 0.0,
        "errors": sum(1 for e in calls if e.get("error")),
        "p95_ms": round(lat[min(len(lat) - 1, int(0.95 * len(lat)))]),
        "dev_pct": round(mean(devs), 1) if devs else None,
        "tokens_per_req": round(mean(e["tokens_in"] + e["tokens_out"] for e in reqs)) if reqs else 0,
        "truncated": sum(e.get("truncated_calls", 0) for e in reqs),
        "agents_errored": sorted({a for e in reqs for a in e.get("agents_errored", [])}),
        "fallback_agents": sorted({a for e in reqs for a in e.get("fallback_agents", [])}),
    }


def git_commit() -> Optional[str]:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        ).stdout.strip() or None
    except Exception:
        return None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--live", action="store_true", help="use real Gemini (GEMINI_API_KEY) instead of the scripted model")
    parser.add_argument("--out", help="output folder (default data/triage/scripted or data/triage/live)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--per-fault", type=int, default=3, help="windows per fault type (default 3)")
    parser.add_argument("--healthy", type=int, default=5, help="healthy windows (default 5)")
    parser.add_argument("--requests", type=int, default=4, help="requests per window (default 4)")
    parser.add_argument("--baseline", type=int, default=2, help="healthy requests before each window (default 2)")
    parser.add_argument("--pace", type=float, default=None, help="seconds between requests (default 0, or 3 with --live)")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output folder")
    args = parser.parse_args(argv)
    if args.pace is None:
        args.pace = 3.0 if args.live else 0.0
    out = args.out or os.path.join(ROOT, "data", "triage", "live" if args.live else "scripted")
    telemetry_path = os.path.join(out, "telemetry.jsonl")
    labels_path = os.path.join(out, "incidents.jsonl")
    if os.path.exists(telemetry_path) and not args.force:
        print(f"{telemetry_path} exists; use --force to overwrite", file=sys.stderr)
        return 2
    os.makedirs(out, exist_ok=True)
    open(telemetry_path, "w").close()

    if not args.live:
        os.environ.setdefault("GEMINI_API_KEY", "not-used-by-the-scripted-model")
    os.environ.pop("K_SERVICE", None)  # faults are hard-off on Cloud Run
    from src.utils.config import settings

    if args.live and settings.gemini_api_key.startswith("not-used"):
        print("--live needs GEMINI_API_KEY", file=sys.stderr)
        return 2
    settings.enable_faults = True
    settings.telemetry_sinks = "file"
    settings.telemetry_file = telemetry_path
    settings.enable_chromadb = False  # its failing setup adds ~2 s per request (see TODO.md)
    settings.enable_llm_router = False
    logging.disable(logging.CRITICAL)  # app logs would only duplicate the telemetry

    runner = Runner(args)
    windows = plan_windows(runner.rng, args.per_fault, args.healthy)
    mode = "live Gemini" if args.live else "scripted model"
    print(f"{len(windows)} windows, {args.baseline}+{args.requests} requests each, {mode}, model {settings.gemini_model}")
    runner.deploy()  # initial revision

    labels = []
    started = time.time()
    for idx, w in enumerate(windows):
        print(f"  [{idx + 1:2d}/{len(windows)}] {w.spec or 'healthy'}{' + deploy' if w.deploy else ''}")
        labels.append(runner.window(idx, w))

    with open(telemetry_path, encoding="utf-8") as fh:
        events = [json.loads(line) for line in fh if line.strip()]
    print(f"\n{'id':8} {'label':18} {'agent':16} {'fallb':>5} {'stub':>5} {'err':>4} {'p95ms':>6} {'dev%':>6} {'tok/req':>7} {'trunc':>5}  agents errored / fell back")
    for label in labels:
        s = summarize(events, label["window_start"], label["window_end"])
        base = summarize(events, label["baseline_start"], label["baseline_end"])
        # A healthy window or baseline with errors would teach the eval wrong lessons.
        label["contaminated"] = bool(
            (label["fault"] is None and (s["errors"] or s["fallback_rate"]))
            or base["errors"] or base["fallback_rate"]
        )
        print(
            f"{label['incident_id']:8} {label['root_cause']:18} {str(label['affected_agent'] or '-'):16} "
            f"{s['fallback_rate']:5.2f} {s['stub_rate']:5.2f} {s['errors']:4d} {s['p95_ms']:6d} "
            f"{str(s['dev_pct']):>6} {s['tokens_per_req']:7d} {s['truncated']:5d}  "
            f"{','.join(s['agents_errored']) or '-'} / {','.join(s['fallback_agents']) or '-'}"
            + ("  CONTAMINATED" if label["contaminated"] else "")
        )

    with open(labels_path, "w", encoding="utf-8") as fh:
        for label in labels:
            fh.write(json.dumps(label) + "\n")
    manifest = {
        "created_at": iso_now(),
        "mode": "live" if args.live else "scripted",
        "model": settings.gemini_model,
        "seed": args.seed,
        "windows": len(labels),
        "requests_per_window": args.requests,
        "baseline_requests": args.baseline,
        "requests_ok": runner.requests_ok,
        "requests_failed": runner.requests_failed,
        "events": len(events),
        "contaminated_windows": [l["incident_id"] for l in labels if l["contaminated"]],
        "git_commit": git_commit(),
        "duration_s": round(time.time() - started, 1),
    }
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"\n{len(labels)} labels -> {labels_path}\n{len(events)} events -> {telemetry_path}")
    if manifest["contaminated_windows"]:
        print(f"warning: contaminated windows {manifest['contaminated_windows']} (real errors during healthy periods)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
