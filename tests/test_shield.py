import pytest
from rate_limit_shield import (
    Shield, TokenBucket, CircuitBreaker, RetryPolicy, CircuitOpen,
)


def _shield(failure_threshold: int = 5, **kw):
    return Shield(
        bucket=TokenBucket(capacity=100, refill_rate=100),
        breaker=CircuitBreaker(failure_threshold=failure_threshold, recovery_timeout=10),
        retry=RetryPolicy(max_attempts=3, base_delay=0.001, jitter=False),
        **kw,
    )


def test_success():
    s = _shield()
    assert s.call(lambda: "ok") == "ok"


def test_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    s = _shield()
    assert s.call(flaky) == "ok"
    assert calls["n"] == 2


def test_breaker_opens_then_blocks():
    # threshold=4 means: first call (3 attempts, 3 failures) leaves count=3, breaker CLOSED.
    # Second call hits 1 more failure -> count=4 -> breaker OPENS -> next attempt blocked.
    s = _shield(failure_threshold=4)

    def boom():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        s.call(boom)
    with pytest.raises(CircuitOpen):
        s.call(boom)
