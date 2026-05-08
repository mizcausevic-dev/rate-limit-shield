"""Exponential backoff with full jitter."""
from __future__ import annotations
import random
from dataclasses import dataclass


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    multiplier: float = 2.0
    jitter: bool = True

    def delay_for(self, attempt: int) -> float:
        if attempt <= 0:
            return 0.0
        d = min(self.max_delay, self.base_delay * (self.multiplier ** (attempt - 1)))
        if self.jitter:
            d = d * (0.5 + random.random() * 0.5)
        return d
