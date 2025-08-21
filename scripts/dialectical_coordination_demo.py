#!/usr/bin/env python
"""Simulate dialectical agent coordination.

Usage:
    uv run scripts/dialectical_coordination_demo.py --loops 5 --trials 100
"""

from __future__ import annotations

import argparse
import random
from statistics import mean, stdev


def run_trial(target: float, loops: int, alpha: float) -> float:
    thesis = random.uniform(target - 1.0, target + 1.0)
    antithesis = random.uniform(target - 1.0, target + 1.0)
    synthesis = (thesis + antithesis) / 2.0
    for _ in range(loops):
        contrarian = synthesis - random.uniform(-0.5, 0.5)
        fact_checker = synthesis + alpha * (target - synthesis)
        synthesis = (synthesis + contrarian + fact_checker) / 3.0
    return synthesis


def main() -> None:
    parser = argparse.ArgumentParser(description="Dialectical coordination demo")
    parser.add_argument("--loops", type=int, default=5, help="Coordination loops")
    parser.add_argument("--trials", type=int, default=100, help="Simulation runs")
    parser.add_argument("--target", type=float, default=1.0, help="Ground truth value")
    parser.add_argument("--alpha", type=float, default=0.5, help="Fact-checker weight")
    args = parser.parse_args()

    results = [run_trial(args.target, args.loops, args.alpha) for _ in range(args.trials)]
    print(f"mean={mean(results):.3f} stdev={stdev(results):.3f}")


if __name__ == "__main__":
    main()
