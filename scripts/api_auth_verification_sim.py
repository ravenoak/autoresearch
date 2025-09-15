"""Verify API authentication invariants via simulation.

Usage:
    uv run scripts/api_auth_verification_sim.py
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import statistics
import timeit
from secrets import compare_digest
from typing import Sequence

EXPECTED_TOKEN = "a" * 32
ROLE_PERMISSIONS = {
    "admin": {"read", "write"},
    "reader": {"read"},
    "anonymous": set(),
}


@dataclass(frozen=True)
class Scenario:
    """Describe a credential scenario to evaluate."""

    name: str
    token: str
    role: str
    action: str
    expected: bool


SCENARIOS: Sequence[Scenario] = (
    Scenario("admin_valid_write", EXPECTED_TOKEN, "admin", "write", True),
    Scenario("admin_invalid_token", "b" * 32, "admin", "write", False),
    Scenario("reader_valid_read", EXPECTED_TOKEN, "reader", "read", True),
    Scenario("reader_invalid_write", EXPECTED_TOKEN, "reader", "write", False),
    Scenario("anonymous_missing_perm", EXPECTED_TOKEN, "anonymous", "read", False),
)


def _wrong_tokens(token: str) -> list[str]:
    """Return same-length tokens differing at each position."""

    return [token[:idx] + "b" + token[idx + 1 :] for idx in range(len(token))]


def _timing_ranges(token: str, *, runs: int = 1000) -> dict[str, float]:
    """Compare naive and constant-time equality timing ranges."""

    wrong_values = _wrong_tokens(token)
    naive_samples = [
        timeit.timeit(lambda t=token, w=wrong: t == w, number=runs) for wrong in wrong_values
    ]
    secure_samples = [
        timeit.timeit(lambda t=token, w=wrong: compare_digest(t, w), number=runs)
        for wrong in wrong_values
    ]
    return {
        "naive_range": max(naive_samples) - min(naive_samples),
        "secure_range": max(secure_samples) - min(secure_samples),
        "naive_stdev": statistics.pstdev(naive_samples),
        "secure_stdev": statistics.pstdev(secure_samples),
    }


def _has_permission(role: str, action: str) -> bool:
    """Return True when ``role`` grants ``action``."""

    return action in ROLE_PERMISSIONS.get(role, set())


def evaluate_scenarios(scenarios: Sequence[Scenario]) -> dict[str, object]:
    """Evaluate credential outcomes and timing deltas."""

    timing = _timing_ranges(EXPECTED_TOKEN)
    observed = []
    mismatches = []
    for scenario in scenarios:
        allowed = compare_digest(scenario.token, EXPECTED_TOKEN) and _has_permission(
            scenario.role, scenario.action
        )
        observed.append({"name": scenario.name, "allowed": allowed})
        if allowed != scenario.expected:
            mismatches.append(scenario.name)

    valid = [case["name"] for case in observed if case["allowed"]]
    invalid = [case["name"] for case in observed if not case["allowed"]]
    return {
        "timing": timing,
        "cases": observed,
        "valid": valid,
        "invalid": invalid,
        "mismatches": mismatches,
    }


def main() -> None:  # pragma: no cover - CLI entry point
    """Run the simulation and pretty-print the results."""

    result = evaluate_scenarios(SCENARIOS)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
