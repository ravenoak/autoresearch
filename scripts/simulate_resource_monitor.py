#!/usr/bin/env python3
"""Run the ResourceMonitor for a short interval.

Usage:
    uv run python scripts/simulate_resource_monitor.py --seconds 2
"""

from __future__ import annotations

import argparse
import time

from autoresearch.resource_monitor import ResourceMonitor


def main(seconds: float) -> None:
    """Sample resource usage for ``seconds`` seconds."""

    monitor = ResourceMonitor(interval=0.5)
    monitor.start()
    time.sleep(seconds)
    monitor.stop()
    cpu = monitor.cpu_gauge._value.get()
    mem = monitor.mem_gauge._value.get()
    print(f"CPU {cpu:.1f}% | MEM {mem:.1f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resource monitor demo")
    parser.add_argument("--seconds", type=float, default=2.0, help="run time")
    args = parser.parse_args()
    main(args.seconds)

