"""Simulate cache eviction under a fixed memory budget.

Usage:
    uv run python scripts/simulate_cache_eviction.py --budget 1024 --steps 100
"""

from __future__ import annotations

import argparse
import random
from collections import OrderedDict


def simulate(budget: int, steps: int) -> None:
    """Run a simple LRU cache simulation."""
    cache: OrderedDict[str, int] = OrderedDict()
    total = 0
    for step in range(steps):
        size = random.randint(1, max(1, budget // 4))
        key = f"k{step}"
        cache[key] = size
        total += size
        cache.move_to_end(key)
        while total > budget and cache:
            _, evicted = cache.popitem(last=False)
            total -= evicted
        print(f"step={step} items={len(cache)} total={total}")
    print(f"final memory {total}/{budget}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=1024, help="memory budget in bytes")
    parser.add_argument("--steps", type=int, default=50, help="number of insertions")
    parser.add_argument("--seed", type=int, default=None, help="optional random seed")
    args = parser.parse_args()
    if args.budget <= 0 or args.steps <= 0:
        raise SystemExit("budget and steps must be positive")
    if args.seed is not None:
        random.seed(args.seed)
    simulate(args.budget, args.steps)


if __name__ == "__main__":
    main()
