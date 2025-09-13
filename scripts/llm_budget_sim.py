"""Simulate token budget adaptation with random workloads.

Usage:
    uv run scripts/llm_budget_sim.py --steps 50 --agents 3 --margin 0.1
"""

from __future__ import annotations

import argparse
import random

from autoresearch.orchestration.metrics import (
    OrchestrationMetrics,
    _mean_last,
    _mean_last_nonzero,
)
from autoresearch.token_budget import round_with_margin


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify token budget bounds with random usage patterns."
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=20,
        help="number of cycles to simulate",
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=2,
        help="number of agents to simulate",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.1,
        help="non-negative budget margin",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="random seed",
    )
    return parser.parse_args()


def _validate(args: argparse.Namespace) -> None:
    if args.steps <= 0 or args.agents <= 0:
        raise SystemExit("steps and agents must be positive")
    if args.margin < 0:
        raise SystemExit("margin must be non-negative")


def main() -> None:
    args = _parse_args()
    _validate(args)

    rng = random.Random(args.seed)
    metrics = OrchestrationMetrics()
    budget = 10
    for step in range(1, args.steps + 1):
        for i in range(args.agents):
            tokens = rng.randint(0, 50)
            if tokens:
                metrics.record_tokens(f"A{i}", tokens, 0)
        suggested = metrics.suggest_token_budget(budget, margin=args.margin)

        latest = metrics.token_usage_history[-1]
        avg_used = _mean_last_nonzero(metrics.token_usage_history)
        max_agent_delta = max(
            (hist[-1] for hist in metrics.agent_usage_history.values()), default=0
        )
        max_agent_avg = max(
            (_mean_last(hist) for hist in metrics.agent_usage_history.values()),
            default=0.0,
        )
        expected = round_with_margin(
            max(latest, avg_used, max_agent_delta, max_agent_avg), args.margin
        )
        expected = max(expected, 1)
        assert suggested == expected, f"bound violated at step {step}"
        budget = suggested
        print(f"step {step}: usage={latest} budget={budget}")
    print(f"final budget: {budget}")


if __name__ == "__main__":
    main()
