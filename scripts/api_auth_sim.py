"""Simulate API auth timing and role checks.

Usage:
    uv run scripts/api_auth_sim.py
"""

from __future__ import annotations

import timeit
from secrets import compare_digest


def _simulate(token: str = "a" * 32) -> dict[str, float | bool]:
    """Return timing ranges and role outcomes for a fixed token."""
    wrong = ["b" * i + "a" * (len(token) - i) for i in range(len(token))]
    naive_times = [timeit.timeit(lambda t=token, w=w: t == w, number=1000) for w in wrong]
    secure_times = [
        timeit.timeit(lambda t=token, w=w: compare_digest(t, w), number=1000) for w in wrong
    ]
    naive_range = max(naive_times) - min(naive_times)
    secure_range = max(secure_times) - min(secure_times)
    permissions = {"admin": {"read", "write"}, "reader": {"read"}}

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
