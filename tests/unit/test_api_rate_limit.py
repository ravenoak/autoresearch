"""Token bucket rate limiting tests.

These tests model a simple token bucket to validate expected behavior and
edge cases such as clock drift.
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest


@dataclass
class _FakeTime:
    """Deterministic clock controllable by tests."""

    value: float = 0.0

    def advance(self, delta: float) -> None:
        self.value += delta

    def __call__(self) -> float:  # pragma: no cover - trivial
        return self.value


class TokenBucket:
    """Minimal token bucket for demonstration purposes."""

    def __init__(self, rate: float, capacity: int, now):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be positive")
        self.rate = rate
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.now = now
        self.last = now()

    def consume(self, amount: float = 1.0) -> bool:
        now = self.now()
        elapsed = max(0.0, now - self.last)
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


def test_initial_burst_and_refill() -> None:
    clock = _FakeTime()
    bucket = TokenBucket(rate=1.0, capacity=2, now=clock)
    assert bucket.consume()
    assert bucket.consume()
    assert not bucket.consume()
    clock.advance(2.0)
    assert bucket.consume()


def test_partial_refill() -> None:
    clock = _FakeTime()
    bucket = TokenBucket(rate=2.0, capacity=1, now=clock)
    assert bucket.consume()
    clock.advance(0.25)  # adds 0.5 token
    assert not bucket.consume()
    clock.advance(0.25)
    assert bucket.consume()


def test_clock_drift() -> None:
    clock = _FakeTime()
    bucket = TokenBucket(rate=1.0, capacity=1, now=clock)
    assert bucket.consume()
    clock.advance(-1.0)  # backward drift should not refill
    assert not bucket.consume()


def test_invalid_parameters() -> None:
    clock = _FakeTime()
    with pytest.raises(ValueError):
        TokenBucket(rate=0, capacity=1, now=clock)
    with pytest.raises(ValueError):
        TokenBucket(rate=1, capacity=0, now=clock)
