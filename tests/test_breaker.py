import time
from rate_limit_shield import CircuitBreaker
from rate_limit_shield.breaker import State


def test_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    for _ in range(3):
        assert cb.allow()
        cb.record_failure()
    assert cb.state == State.OPEN
    assert cb.allow() is False


def test_half_open_after_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
    for _ in range(2):
        cb.allow()
        cb.record_failure()
    time.sleep(0.06)
    assert cb.allow() is True
    assert cb.state == State.HALF_OPEN


def test_recovery_closes():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
    for _ in range(2):
        cb.allow()
        cb.record_failure()
    time.sleep(0.06)
    cb.allow()
    cb.record_success()
    assert cb.state == State.CLOSED
