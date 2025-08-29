#!/usr/bin/env python3
"""Run orchestration simulations to illustrate deterministic behavior.

Usage:
    uv run python scripts/orchestration_sim.py circuit
    uv run python scripts/orchestration_sim.py parallel
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from autoresearch.orchestration.circuit_breaker import simulate_circuit_breaker


def circuit_breaker_sim() -> List[str]:
    """Return breaker states for a deterministic event sequence."""

    events = ["critical", "critical", "critical", "tick", "success"]
    return simulate_circuit_breaker(events, threshold=3, cooldown=1)


def parallel_execution_sim() -> Dict[str, str]:
    """Run a deterministic parallel aggregation example."""

    groups = ["A", "B", "C"]

    def run(name: str) -> str:
        time.sleep(0.01 * (ord(name) - ord("A")))
        return f"claim-{name}"

    results: Dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=len(groups)) as executor:
        futures = {executor.submit(run, g): g for g in groups}
        for fut in as_completed(futures):
            group_name = futures[fut]
            results[group_name] = fut.result()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestration simulations.")
    parser.add_argument("mode", choices=["circuit", "parallel"], help="simulation to run")
    args = parser.parse_args()

    if args.mode == "circuit":
        print(circuit_breaker_sim())
    else:
        print(parallel_execution_sim())


if __name__ == "__main__":
    main()
