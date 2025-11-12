"""Metrics collection and session aggregation utilities for the Email Assistant.

This module is deliberately lightweight and dependency-free. It provides a
singleton-style MetricsManager that accumulates per-call usage statistics for
LLM activity (requests, tokens, latency, cost) and exposes a simple API for
retrieving summaries suitable for display in the Streamlit UI or for tracing.

The manager is safe to import even if cost tracking is disabled; all methods
become no-ops when the feature toggle is off.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from .config import settings, pricing_for_model

_lock = threading.Lock()
_start_time = time.time()

@dataclass
class CallRecord:
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

class MetricsManager:
    """Aggregates metrics for the current process/session.

    Usage:
        from src.utils.metrics import metrics
        metrics.record_call(model="gemini-2.0-flash", latency_ms=120.5, input_tokens=100, output_tokens=180, cost_usd=0.0002)
        summary = metrics.session_summary()
    """
    def __init__(self) -> None:
        self._calls: list[CallRecord] = []
        self._session_id = f"session_{int(_start_time)}"

    def enabled(self) -> bool:
        """Metrics collection is always enabled; cost computation is conditional.

        We always track requests/tokens/latency for observability. Cost is only
        computed when settings.enable_cost_tracking is True.
        """
        return True

    def record_call(
        self,
        model: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        error: Optional[str] = None,
    ) -> None:
        with _lock:
            self._calls.append(CallRecord(model, latency_ms, input_tokens, output_tokens, cost_usd, error))

    def session_summary(self) -> Dict:
        with _lock:
            total_requests = len(self._calls)
            successful = sum(1 for c in self._calls if not c.error)
            total_input = sum(c.input_tokens for c in self._calls)
            total_output = sum(c.output_tokens for c in self._calls)
            total_cost = sum(c.cost_usd for c in self._calls)
            avg_latency = (sum(c.latency_ms for c in self._calls) / total_requests) if total_requests else 0.0
            errors = sum(1 for c in self._calls if c.error)
        return {
            "session_id": self._session_id,
            "llm_calls": total_requests,  # renamed for clarity: this is LLM API calls, not user requests
            "successful_calls": successful,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "estimated_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
            "errors": errors,
            "feature_enabled": True,
            "cost_tracking_enabled": bool(settings.enable_cost_tracking),
        }

    def last_call(self) -> Optional[Dict]:
        """Return the most recent call metrics for quick UI display."""
        with _lock:
            if not self._calls:
                return None
            record = self._calls[-1]
        return {
            "model": record.model,
            "latency_ms": record.latency_ms,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "cost_usd": record.cost_usd,
            "error": record.error,
            "timestamp": record.timestamp,
        }

    def compute_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = pricing_for_model(model)
        # Convert per-million pricing to per token cost
        in_cost = (pricing["input_per_million"] / 1_000_000.0) * input_tokens
        out_cost = (pricing["output_per_million"] / 1_000_000.0) * output_tokens
        return in_cost + out_cost

    def flush_to_disk(self, path: Optional[str] = None) -> Optional[str]:
        """Persist current metrics to a JSON file. Returns the file path or None if disabled."""
        output_dir = settings.metrics_output_dir
        os.makedirs(output_dir, exist_ok=True)
        file_path = path or os.path.join(output_dir, f"{self._session_id}.json")
        with _lock:
            payload = {
                "session": self.session_summary(),
                "calls": [c.__dict__ for c in self._calls],
            }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return file_path

# Global singleton
metrics = MetricsManager()

__all__ = ["metrics", "MetricsManager", "CallRecord"]
