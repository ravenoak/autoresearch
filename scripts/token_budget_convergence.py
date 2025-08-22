#!/usr/bin/env python
"""Demonstrate convergence of suggest_token_budget.

Usage:
    uv run scripts/token_budget_convergence.py --steps 10 --usage 50
"""

from __future__ import annotations

import argparse
from typing import List

from autoresearch.orchestration.metrics import OrchestrationMetrics


def simulate(steps: int, usage: int) -> List[int]:
    m = OrchestrationMetrics()
    budget = usage
    budgets: List[int] = []
    for _ in range(steps):
        m.token_usage_history.append(usage)
        budget = m.suggest_token_budget(budget)
        budgets.append(budget)
    return budgets


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate token budget convergence")
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--usage", type=int, default=50)
    args = parser.parse_args()
    budgets = simulate(args.steps, args.usage)
    for i, b in enumerate(budgets, start=1):
        print(f"step {i}: {b}")
    print(f"final budget: {budgets[-1]}")


if __name__ == "__main__":
    main()
