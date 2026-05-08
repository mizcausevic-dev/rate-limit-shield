"""LLM-aware shield: per-model quotas, HTTP 429 / Retry-After awareness."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .bucket import TokenBucket
from .breaker import CircuitBreaker
from .retry import RetryPolicy
from .shield import Shield


def parse_retry_after(headers: Dict[str, str]) -> float:
    """Honor Retry-After (delta-seconds form). Returns 0.0 if absent/invalid."""
    if not headers:
        return 0.0
    ra = headers.get("retry-after") or headers.get("Retry-After")
    if ra is None:
        return 0.0
    try:
        return max(0.0, float(ra))
    except (TypeError, ValueError):
        return 0.0


@dataclass
class LLMShield:
    """Per-model rate limiting. RPM = requests/min, TPM reserved for future use."""
    rpm_limits: Dict[str, int] = field(default_factory=dict)
    tpm_limits: Dict[str, int] = field(default_factory=dict)
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    max_retries: int = 3

    _shields: Dict[str, Shield] = field(default_factory=dict, init=False)

    def shield_for(self, model: str) -> Shield:
        if model not in self._shields:
            rpm = self.rpm_limits.get(model, 60)
            self._shields[model] = Shield(
                bucket=TokenBucket(capacity=rpm, refill_rate=rpm / 60.0),
                breaker=CircuitBreaker(
                    failure_threshold=self.failure_threshold,
                    recovery_timeout=self.recovery_timeout,
                ),
                retry=RetryPolicy(max_attempts=self.max_retries),
            )
        return self._shields[model]

    def state_snapshot(self) -> Dict[str, Dict[str, object]]:
        return {
            model: {
                "available_tokens": s.bucket.available,
                "breaker_state": s.breaker.state.value,
            }
            for model, s in self._shields.items()
        }
