"""Sample layout times for varying node counts.

Usage:
    uv run --with scipy scripts/visualization_performance.py [COUNTS ...]

The script prints a table of node counts and seconds required to compute
spring layout. Counts default to 10 50 100 200 500.
"""

from __future__ import annotations

import argparse
import time

import networkx as nx


def measure(counts: list[int]) -> list[tuple[int, float]]:
    results: list[tuple[int, float]] = []
    nx.spring_layout(nx.empty_graph(2), seed=42)
    for n in counts:
        graph = nx.gnm_random_graph(n, n * 2, seed=42)
        start = time.perf_counter()
        nx.spring_layout(graph, seed=42)
        duration = time.perf_counter() - start
        results.append((n, duration))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample layout times for node counts.")
    parser.add_argument(
        "counts",
        nargs="*",
        type=int,
        default=[10, 50, 100, 200, 500],
        help="Node counts to sample.",
    )
    args = parser.parse_args()
    for n, secs in measure(args.counts):
        print(f"{n} {secs:.6f}")


if __name__ == "__main__":
    main()
