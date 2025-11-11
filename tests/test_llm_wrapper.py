import time
import pytest

from src.utils.llm_wrapper import LLMWrapper


class DummyError(Exception):
    pass


def test_run_with_retries_exponential_backoff(monkeypatch):
    calls = {"count": 0}

    def flaky_call():
        calls["count"] += 1
        if calls["count"] < 3:
            raise DummyError("temporary failure")
        return "ok"

    wrapper = LLMWrapper(llm=None, max_retries=3, initial_backoff=0.01, backoff_factor=1.0, max_backoff=0.05)

    start = time.time()
    result = wrapper.run_with_retries(flaky_call)
    elapsed = time.time() - start

    assert result == "ok"
    assert calls["count"] == 3
    # elapsed should be small due to tiny backoff
    assert elapsed < 0.5


def test_run_with_retries_server_suggested_delay(monkeypatch):
    calls = {"count": 0}

    class Suggested(Exception):
        def __str__(self):
            return "Please retry in 0.02s"

    def flaky_call():
        calls["count"] += 1
        if calls["count"] < 2:
            raise Suggested()
        return "ok"

    wrapper = LLMWrapper(llm=None, max_retries=2, initial_backoff=0.5, backoff_factor=10.0, max_backoff=0.5)

    start = time.time()
    result = wrapper.run_with_retries(flaky_call)
    elapsed = time.time() - start

    assert result == "ok"
    assert calls["count"] == 2
    # Because of server-suggested 0.02s, elapsed should be well below the large defaults
    assert elapsed < 0.3


def test_run_with_retries_exhaustion_raises():
    def always_fail():
        raise DummyError("permanent")

    wrapper = LLMWrapper(llm=None, max_retries=1, initial_backoff=0.01, backoff_factor=1.0, max_backoff=0.05)

    with pytest.raises(Exception):
        wrapper.run_with_retries(always_fail)
