"""Simulate LLM adapter switching and token budgeting.

Usage:
    uv run python scripts/simulate_llm_adapter.py "prompt text" \
        --adapters dummy openai --budget 50
"""

from __future__ import annotations

import argparse
from typing import List

from autoresearch.llm import get_llm_adapter
from autoresearch.llm.token_counting import compress_prompt


def simulate(prompt: str, adapters: List[str], budget: int) -> None:
    """Select the first adapter whose compressed prompt fits the budget."""
    for name in adapters:
        adapter = get_llm_adapter(name)
        compressed = compress_prompt(prompt, budget)
        tokens = len(compressed.split())
        print(f"{name}: {tokens}/{budget} tokens")
        if tokens <= budget:
            print(f"selected {name}")
            break
    else:
        print("no adapter met the token budget")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="prompt text to evaluate")
    parser.add_argument(
        "--adapters",
        nargs="+",
        default=["dummy"],
        help="ordered adapter names to try",
    )
    parser.add_argument("--budget", type=int, default=100, help="token budget for prompt")
    args = parser.parse_args()
    if args.budget <= 0:
        raise SystemExit("budget must be positive")
    if not args.adapters:
        raise SystemExit("provide at least one adapter")
    simulate(args.prompt, args.adapters, args.budget)


if __name__ == "__main__":
    main()
