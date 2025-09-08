#!/usr/bin/env python3
"""Simulate config hot reload and verify invariants.

Usage:
    uv run scripts/config_hot_reload_sim.py --updates 1 2 3 4
"""

from __future__ import annotations

import argparse
import logging
from typing import Callable, Iterable


log = logging.getLogger(__name__)


def is_valid(value: int) -> bool:
    """Check whether a configuration value is valid."""
    return value % 2 == 0


def simulate_reload(
    updates: Iterable[int],
    *,
    validator: Callable[[int], bool] = is_valid,
) -> int:
    """Process a sequence of config updates.

    Args:
        updates: Iterable of candidate config values.
        validator: Function validating each candidate.

    Returns:
        Final active configuration.

    Raises:
        AssertionError: If invariants are violated.
    """
    active = 0
    for candidate in updates:
        previous = active
        if validator(candidate):
            active = candidate
        else:
            log.warning("Invalid config value: %s", candidate)
        # Invariant 1: active config is always valid.
        assert validator(active)
        # Invariant 2: invalid updates do not change the active config.
        if not validator(candidate):
            assert active == previous
    return active


def main() -> None:
    """Run the simulation from the command line."""
    parser = argparse.ArgumentParser(description="Simulate config hot reload")
    parser.add_argument(
        "--updates",
        nargs="*",
        type=int,
        default=[1, 2, 3, 4],
        help="Sequence of config values",
    )
    args = parser.parse_args()
    final = simulate_reload(args.updates)
    print(f"final config: {final}")


if __name__ == "__main__":
    main()
