#!/usr/bin/env python
"""Compare token metrics with baselines and enforce a threshold."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _total(tokens: dict[str, dict[str, int]]) -> int:
    return sum(v.get("in", 0) + v.get("out", 0) for v in tokens.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check token usage regression")
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Allowed increase in total tokens compared to baseline",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("tests/integration/baselines/token_usage.json"),
    )
    parser.add_argument(
        "--release-metrics",
        type=Path,
        default=Path("tests/integration/baselines/release_tokens.json"),
    )
    parser.add_argument(
        "--release",
        default=os.getenv("AUTORESEARCH_RELEASE", "development"),
    )
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text())
    metrics_data = json.loads(args.release_metrics.read_text())
    metrics = metrics_data.get(args.release)
    if metrics is None:
        print(f"No metrics recorded for release {args.release}")
        return 0

    baseline_total = _total(baseline)
    latest_total = _total(metrics)

    if latest_total > baseline_total + args.threshold:
        print(
            f"Token usage {latest_total} exceeds baseline {baseline_total} + {args.threshold}"
        )
        return 1

    print("Token usage within threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
