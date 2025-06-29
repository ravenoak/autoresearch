#!/usr/bin/env python
"""Optimize search ranking weights using evaluation data."""

import argparse
from pathlib import Path

import tomllib
import tomli_w

from autoresearch.search import Search


def update_config(cfg_path: Path, weights: tuple[float, float, float]) -> None:
    """Write tuned weights back to a TOML configuration file."""
    data = tomllib.loads(cfg_path.read_text())
    search_cfg = data.setdefault("search", {})
    search_cfg["semantic_similarity_weight"] = round(weights[0], 2)
    search_cfg["bm25_weight"] = round(weights[1], 2)
    search_cfg["source_credibility_weight"] = round(weights[2], 2)
    cfg_path.write_text(tomli_w.dumps(data))


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune search ranking weights")
    parser.add_argument("dataset", type=Path, help="Path to evaluation CSV")
    parser.add_argument("config", type=Path, help="Path to config TOML to update")
    parser.add_argument(
        "--step",
        type=float,
        default=0.1,
        help="Grid search step size between 0 and 1",
    )
    args = parser.parse_args()

    data = Search.load_evaluation_data(args.dataset)
    weights = Search.tune_weights(data, step=args.step)
    score = Search.evaluate_weights(weights, data)
    print(
        f"Best weights: semantic={weights[0]:.2f}, bm25={weights[1]:.2f}, "
        f"cred={weights[2]:.2f} (NDCG={score:.3f})"
    )
    update_config(args.config, weights)


if __name__ == "__main__":
    main()
