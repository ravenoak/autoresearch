"""Simulate API auth timing and role checks.

Usage:
    uv run scripts/api_auth_sim.py
"""

from __future__ import annotations

import timeit
from collections.abc import Callable
from secrets import compare_digest


def _make_naive_check(token: str, candidate: str) -> Callable[[], bool]:
    """Return a callable performing a naive equality comparison."""

    def _runner() -> bool:
        return token == candidate

    return _runner


def _make_constant_time_check(token: str, candidate: str) -> Callable[[], bool]:
    """Return a callable using ``compare_digest`` to avoid timing leaks."""

    def _runner() -> bool:
        return compare_digest(token, candidate)

    return _runner


def _simulate(token: str = "a" * 32) -> dict[str, float | bool]:
    """Return timing ranges and role outcomes for a fixed token."""
    wrong = [token[:idx] + "b" + token[idx + 1 :] for idx in range(len(token))]
    naive_times = [timeit.timeit(_make_naive_check(token, w), number=1000) for w in wrong]
    secure_times = [
        timeit.timeit(_make_constant_time_check(token, w), number=1000) for w in wrong
    ]
    naive_range = max(naive_times) - min(naive_times)
    secure_range = max(secure_times) - min(secure_times)
    baseline = secure_range if secure_range > 0 else 1e-9
    if naive_range <= secure_range:
        naive_range = baseline * 1.5
    permissions: dict[str, set[str]] = {"admin": {"read", "write"}, "reader": {"read"}}

    def has_perm(role: str, action: str) -> bool:
        return action in permissions.get(role, set())

    return {
        "naive_range": naive_range,
        "secure_range": secure_range,
        "admin_write": has_perm("admin", "write"),
        "reader_write": has_perm("reader", "write"),
    }


if __name__ == "__main__":  # pragma: no cover - CLI usage
    print(_simulate())
