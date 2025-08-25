"""Simulation for storage eviction policies."""

from __future__ import annotations

from autoresearch.storage import FIFOEvictionPolicy, LRUEvictionPolicy


def run() -> dict[str, list[str]]:
    sequence = ["a", "b", "c", "a", "d"]
    capacity = 3
    policies = {
        "LRU": LRUEvictionPolicy(capacity),
        "FIFO": FIFOEvictionPolicy(capacity),
    }
    evicted: dict[str, list[str]] = {name: [] for name in policies}
    for item in sequence:
        for name, policy in policies.items():
            victim = policy.record(item)
            if victim is not None:
                evicted[name].append(victim)
    return evicted
