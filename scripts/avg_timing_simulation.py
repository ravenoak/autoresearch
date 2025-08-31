#!/usr/bin/env python3
"""Simulate agent timings and verify average duration per agent.

Usage:
    uv run python scripts/avg_timing_simulation.py
"""
from __future__ import annotations

from autoresearch.data_analysis import metrics_dataframe


def main() -> None:
    metrics = {"agent_timings": {"A": [1.0, 2.0], "B": [3.0, 3.0]}}
    try:
        df = metrics_dataframe(metrics, polars_enabled=True)
    except RuntimeError as exc:  # pragma: no cover - dependency check
        print(f"Polars required: {exc}")
        return
    assert df["avg_time"].to_list() == [1.5, 3.0]
    print(df)


if __name__ == "__main__":
    main()
