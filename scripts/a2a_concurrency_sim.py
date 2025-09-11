#!/usr/bin/env python3
"""Simulate race-free A2A dispatch.

Usage:
    uv run scripts/a2a_concurrency_sim.py --agents 3 --tasks 5

Assumptions:
- a single global :class:`~threading.Lock` protects the dispatch map
- tasks are independent of one another

Outcomes:
- each agent receives ``tasks`` assignments
- the total equals ``agents * tasks``
- a global counter yields a total event order

See docs/specs/a2a-interface.md for invariants.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Tuple


@dataclass
class SimulationResult:
    """Summary of dispatch outcomes."""

    total_dispatched: int
    agent_counts: Dict[int, int]
    dispatch_log: List[Tuple[int, int]] = field(default_factory=list)


def run_simulation(agents: int, tasks: int) -> SimulationResult:
    """Dispatch ``tasks`` to each agent concurrently without races."""
    if agents <= 0 or tasks <= 0:
        raise ValueError("agents and tasks must be positive")

    lock = Lock()
    agent_counts: Dict[int, int] = {a: 0 for a in range(agents)}
    total = 0
    event_id = 0
    dispatch_log: List[Tuple[int, int]] = []

    def dispatch(agent_id: int) -> None:
        nonlocal total, event_id
        with lock:
            agent_counts[agent_id] += 1
            dispatch_log.append((event_id, agent_id))
            event_id += 1
            total += 1

    with ThreadPoolExecutor(max_workers=agents) as ex:
        for agent_id in range(agents):
            for _ in range(tasks):
                ex.submit(dispatch, agent_id)

    return SimulationResult(
        total_dispatched=total,
        agent_counts=agent_counts,
        dispatch_log=dispatch_log,
    )


def main(agents: int, tasks: int) -> None:
    """Run the simulation, validate invariants, and print the result."""
    result = run_simulation(agents, tasks)
    expected = agents * tasks
    assert result.total_dispatched == expected
    assert sum(result.agent_counts.values()) == expected
    assert all(count == tasks for count in result.agent_counts.values())
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", type=int, default=2, help="number of agents")
    parser.add_argument("--tasks", type=int, default=5, help="tasks per agent")
    args = parser.parse_args()
    main(args.agents, args.tasks)
