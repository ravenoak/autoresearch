"""Unit tests for :mod:`autoresearch.error_recovery`."""
from __future__ import annotations

import time

import pytest

from autoresearch.error_recovery import retry_with_backoff


def test_retry_with_backoff_succeeds_on_first_try(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return after a single attempt when the action succeeds immediately."""
    attempts: list[int] = []

    def action() -> bool:
        attempts.append(1)
        return True

    monkeypatch.setattr(time, "sleep", lambda _delay: None)

    count = retry_with_backoff(action, max_retries=3, base_delay=0.01)

    assert count == 1
    assert len(attempts) == 1


def test_retry_with_backoff_retries_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retry until the action succeeds before reaching the retry limit."""
    responses = iter([False, False, True])

    def action() -> bool:
        return next(responses)

    monkeypatch.setattr(time, "sleep", lambda _delay: None)

    count = retry_with_backoff(action, max_retries=5, base_delay=0.01)

    assert count == 3


def test_retry_with_backoff_raises_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise ``RuntimeError`` when the action never succeeds."""
    monkeypatch.setattr(time, "sleep", lambda _delay: None)

    def action() -> bool:
        return False

    with pytest.raises(RuntimeError):
        retry_with_backoff(action, max_retries=2, base_delay=0.01)
