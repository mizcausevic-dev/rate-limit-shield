import time
import pytest
from rate_limit_shield import TokenBucket


def test_starts_full():
    b = TokenBucket(capacity=10, refill_rate=1.0)
    assert b.try_acquire(10) is True
    assert b.try_acquire(1) is False


def test_refills():
    b = TokenBucket(capacity=10, refill_rate=100.0)
    b.try_acquire(10)
    time.sleep(0.05)
    assert b.try_acquire(1) is True


def test_wait_time_estimates():
    b = TokenBucket(capacity=10, refill_rate=10.0)
    b.try_acquire(10)
    w = b.wait_time(5)
    assert 0.4 < w < 0.6


def test_invalid_args():
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_rate=1)
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate=0)
