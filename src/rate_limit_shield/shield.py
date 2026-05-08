"""Composable shield: bucket + breaker + retry."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .bucket import TokenBucket
from .breaker import CircuitBreaker
from .retry import RetryPolicy


class RateLimited(Exception):
    """Raised when bucket cannot fulfill request within budget."""


class CircuitOpen(Exception):
    """Raised when circuit breaker is open."""


@dataclass
class Shield:
    bucket: TokenBucket
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    retry: RetryPolicy = field(default_factory=RetryPolicy)

    def call(self, fn: Callable[..., Any], *args: Any, tokens: float = 1.0, **kwargs: Any) -> Any:
        last_exc: Optional[BaseException] = None
        for attempt in range(self.retry.max_attempts):
            if not self.breaker.allow():
                raise CircuitOpen("Circuit breaker is OPEN")

            wait = self.bucket.wait_time(tokens)
            if wait > 0:
                time.sleep(wait)
            self.bucket.try_acquire(tokens)

            try:
                result = fn(*args, **kwargs)
                self.breaker.record_success()
                return result
            except Exception as e:
                last_exc = e
                self.breaker.record_failure()
                if attempt < self.retry.max_attempts - 1:
                    time.sleep(self.retry.delay_for(attempt + 1))

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Retry budget exhausted with no exception captured")
