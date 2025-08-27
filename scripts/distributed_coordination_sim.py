#!/usr/bin/env python3
"""Simulate leader election and FIFO message ordering.

Usage:
    uv run python scripts/distributed_coordination_sim.py --nodes 3 --messages 5
"""

from __future__ import annotations

import argparse
import random
from typing import Iterable, List

from autoresearch.distributed.broker import InMemoryBroker


def elect_leader(node_ids: Iterable[int]) -> int:
    """Return the lowest identifier as the leader."""
    ids = list(node_ids)
    if not ids:
        raise ValueError("node_ids must be non-empty")
    return min(ids)


def process_messages(messages: List[str]) -> List[str]:
    """Publish messages to an in-memory broker and collect them in order."""
    broker = InMemoryBroker()
    for msg in messages:
        broker.publish({"data": msg})
    ordered: List[str] = []
    while not broker.queue.empty():
        ordered.append(broker.queue.get()["data"])
    broker.shutdown()
    return ordered


def main(nodes: int, messages: int) -> None:
    """Run the simulation with ``nodes`` and ``messages`` parameters."""
    if nodes <= 0 or messages < 0:
        raise SystemExit("nodes must be > 0 and messages >= 0")

    node_ids = list(range(nodes))
    random.shuffle(node_ids)
    leader = elect_leader(node_ids)
    print(f"leader: {leader}")

    msgs = [f"{nid}-{i}" for nid in node_ids for i in range(messages)]
    delivered = process_messages(msgs)
    print("first messages:", delivered[:5])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed coordination simulation")
    parser.add_argument("--nodes", type=int, default=3, help="number of nodes")
    parser.add_argument("--messages", type=int, default=5, help="messages per node")
    args = parser.parse_args()
    main(args.nodes, args.messages)
