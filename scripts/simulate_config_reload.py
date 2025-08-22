#!/usr/bin/env python
"""Demonstrate configuration hot reload by watching a file.

Usage:
    uv run scripts/simulate_config_reload.py /tmp/cfg.txt --updates 3

The script prints a message every time the file changes and simulates
updates by rewriting it.
"""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path


def watch(path: Path, interval: float, stop: threading.Event) -> None:
    """Poll ``path`` and print its contents when it changes."""
    last = path.stat().st_mtime
    while not stop.is_set():
        current = path.stat().st_mtime
        if current != last:
            last = current
            print(f"reload: {path.read_text().strip()}")
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate hot reload via file polling",
    )
    parser.add_argument("path", type=Path, help="path to config file")
    parser.add_argument(
        "--updates",
        type=int,
        default=3,
        help="number of simulated updates",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="poll interval in seconds",
    )
    args = parser.parse_args()
    if args.updates <= 0 or args.interval <= 0:
        parser.error("updates and interval must be positive")
    if not args.path.exists():
        args.path.write_text("0\n")
    stop = threading.Event()
    watcher = threading.Thread(
        target=watch,
        args=(args.path, args.interval, stop),
        daemon=True,
    )
    watcher.start()
    for i in range(args.updates):
        args.path.write_text(f"{i + 1}\n")
        time.sleep(args.interval / 2)
    stop.set()
    watcher.join()


if __name__ == "__main__":
    main()
