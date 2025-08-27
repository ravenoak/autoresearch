"""Simulate circuit breaker and parallel result merging.

Usage:
    uv run python scripts/orchestration_sim.py
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager


def simulate_circuit_breaker() -> None:
    """Show threshold trip and recovery."""

    mgr = CircuitBreakerManager(threshold=3, cooldown=1)
    for _ in range(3):
        mgr.update_circuit_breaker("agent", "critical")
    print("After failures:", mgr.get_circuit_breaker_state("agent"))
    time.sleep(1.1)
    mgr.circuit_breakers["agent"]["state"] = "half-open"
    mgr.handle_agent_success("agent")
    print("After recovery:", mgr.get_circuit_breaker_state("agent"))


def simulate_parallel_merge() -> None:
    """Run dummy groups in parallel and merge results."""

    groups = [["a1"], ["b1", "b2"], ["c1"]]

    def run_group(group: list[str]) -> str:
        time.sleep(0.05 * len(group))
        return " ".join(group)

    results: list[tuple[list[str], str]] = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_group, g): g for g in groups}
        for fut in as_completed(futures):
            grp = futures[fut]
            results.append((grp, fut.result()))

    merged = {" ".join(grp): res for grp, res in results}
    print("Merged:", merged)


def main() -> None:
    """Run both simulations."""

    simulate_circuit_breaker()
    simulate_parallel_merge()


if __name__ == "__main__":
    main()
