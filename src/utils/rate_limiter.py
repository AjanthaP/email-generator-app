"""Client-side rate limiting utilities.

Implements a lightweight sliding window + concurrency guard. It is intentionally
best-effort: if anything goes wrong, it falls back to allowing the request.

Features:
- Requests per minute cap (RPM)
- Approximate tokens per minute cap (TPM) using estimates provided by wrapper
- Simple concurrency control (max simultaneous in-flight calls)
- Jitter to reduce herd effects when many retries happen at once

Usage:
    from src.utils.rate_limiter import RateLimiter
    limiter = RateLimiter(rpm=30, tpm=60000, max_concurrency=4)
    limiter.acquire(estimated_input_tokens)

The acquire() method will block until allowance is available or raise after an
extended wait (currently it does not raise; it just waits).
"""
from __future__ import annotations

import threading
import time
import random
from collections import deque
from typing import Deque

class RateLimiter:
    def __init__(
        self,
        rpm: int,
        tpm: int,
        max_concurrency: int,
        jitter_ms: int = 150,
    ) -> None:
        self.rpm = max(1, rpm)
        self.tpm = max(1, tpm)
        self.max_concurrency = max(1, max_concurrency)
        self.jitter_ms = max(0, jitter_ms)
        self._lock = threading.Lock()
        self._req_timestamps: Deque[float] = deque()
        self._token_timestamps: Deque[tuple[float, int]] = deque()
        self._in_flight = 0

    def _purge(self, now: float) -> None:
        one_minute_ago = now - 60.0
        while self._req_timestamps and self._req_timestamps[0] < one_minute_ago:
            self._req_timestamps.popleft()
        while self._token_timestamps and self._token_timestamps[0][0] < one_minute_ago:
            self._token_timestamps.popleft()

    def acquire(self, estimated_input_tokens: int) -> None:
        """Block until request is permitted under RPM/TPM/concurrency.

        estimated_input_tokens: rough estimate provided by caller.
        """
        est_tokens = max(0, estimated_input_tokens)
        while True:
            with self._lock:
                now = time.time()
                self._purge(now)
                # Check concurrency
                if self._in_flight >= self.max_concurrency:
                    wait = 0.05
                else:
                    # RPM check
                    if len(self._req_timestamps) >= self.rpm:
                        # Wait until earliest request exits window
                        earliest = self._req_timestamps[0]
                        wait = max(0.01, (earliest + 60.0) - now)
                    else:
                        # TPM check
                        token_used_last_min = sum(t for _, t in self._token_timestamps)
                        if token_used_last_min + est_tokens > self.tpm:
                            # Wait until some tokens fall out of window
                            # Approx: find earliest that frees enough tokens
                            cumulative = 0
                            wait_until = None
                            for ts, tok in self._token_timestamps:
                                cumulative += tok
                                if token_used_last_min - cumulative + est_tokens <= self.tpm:
                                    wait_until = ts + 60.0
                                    break
                            if wait_until is None:
                                # Fallback small wait
                                wait = 0.25
                            else:
                                wait = max(0.01, wait_until - now)
                        else:
                            # Allowed
                            self._req_timestamps.append(now)
                            if est_tokens:
                                self._token_timestamps.append((now, est_tokens))
                            self._in_flight += 1
                            # Release lock and return
                            break
            # Sleep outside lock
            # Add jitter
            jitter = random.uniform(0, self.jitter_ms / 1000.0) if self.jitter_ms else 0.0
            time.sleep(wait + jitter)

    def release(self) -> None:
        with self._lock:
            if self._in_flight > 0:
                self._in_flight -= 1

    def __enter__(self):  # context manager for manual usage if desired
        self.acquire(0)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()

__all__ = ["RateLimiter"]
