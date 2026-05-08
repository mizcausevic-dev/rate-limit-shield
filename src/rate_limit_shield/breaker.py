"""Circuit breaker (closed -> open -> half-open -> closed)."""
from __future__ import annotations
import time
import threading
from enum import Enum
from dataclasses import dataclass, field


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1

    state: State = field(default=State.CLOSED)
    _failures: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def allow(self) -> bool:
        with self._lock:
            if self.state == State.CLOSED:
                return True
            if self.state == State.OPEN:
                if time.monotonic() - self._opened_at >= self.recovery_timeout:
                    self.state = State.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    return False
            if self.state == State.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            return False

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self.state = State.CLOSED
            self._half_open_calls = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self.state == State.HALF_OPEN or self._failures >= self.failure_threshold:
                self.state = State.OPEN
                self._opened_at = time.monotonic()
                self._half_open_calls = 0
