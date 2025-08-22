#!/usr/bin/env python
"""Compare token metrics or coverage against baselines and enforce thresholds.

Usage:
    uv run python scripts/check_token_regression.py --threshold 5
    uv run python scripts/check_token_regression.py \
        --coverage-current current/coverage.xml
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET


def _total(tokens: dict[str, dict[str, int]]) -> int:
    return sum(v.get("in", 0) + v.get("out", 0) for v in tokens.values())


def _coverage_percent(path: Path) -> float:
    tree = ET.fromstring(path.read_text())
    return float(tree.get("line-rate", "0")) * 100


def main() -> int:
    parser = argparse.ArgumentParser(description="Check token or coverage regression")
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Allowed change in metric compared to baseline",
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
    parser.add_argument(
        "--coverage-baseline",
        type=Path,
        default=Path("baseline/coverage.xml"),
        help="Path to baseline coverage XML",
    )
    parser.add_argument(
        "--coverage-current",
        type=Path,
        help="Path to current coverage XML",
    )
    args = parser.parse_args()

    if args.coverage_current:
        if not args.coverage_current.exists():
            parser.error(f"Coverage file not found: {args.coverage_current}")
        if not args.coverage_baseline.exists():
            print(f"No baseline coverage at {args.coverage_baseline}")
            return 0
        baseline_cov = _coverage_percent(args.coverage_baseline)
        current_cov = _coverage_percent(args.coverage_current)
        if current_cov + args.threshold < baseline_cov:
            print(
                f"Coverage {current_cov:.2f}% below baseline "
                f"{baseline_cov:.2f}% - {args.threshold}% allowed"
            )
            return 1
        print("Coverage within threshold")
        return 0

    baseline = json.loads(args.baseline.read_text())
    metrics_data = json.loads(args.release_metrics.read_text())
    metrics = metrics_data.get(args.release)
    if metrics is None:
        print(f"No metrics recorded for release {args.release}")
        return 0

    baseline_total = _total(baseline)
    latest_total = _total(metrics)

    if latest_total > baseline_total + args.threshold:
        print(f"Token usage {latest_total} exceeds baseline {baseline_total} + {args.threshold}")
        return 1

    print("Token usage within threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
