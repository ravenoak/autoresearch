#!/usr/bin/env python3
"""Simulate API streaming to validate ordering and heartbeat invariants.

Usage:
    uv run python scripts/api_stream_order_sim.py --chunks 3 --output metrics.json

The simulation sends ``chunks`` messages and interleaved heartbeats, recording
metrics about ordering and liveness.
"""
from __future__ import annotations

import argparse
import json
from typing import Dict


def _simulate(chunks: int) -> Dict[str, object]:
    """Stream chunks and heartbeats, returning metrics.

    Args:
        chunks: Number of data chunks to stream.
    """

    sent = [f"chunk-{i}" for i in range(chunks)]
    heartbeats = chunks  # model at least one heartbeat per chunk
    sent.append("END")
    ordered = sent == sorted(sent[:-1]) + ["END"]
    operations = len(sent) + heartbeats
    return {"ordered": ordered, "heartbeats": heartbeats, "operations": operations}


def main(chunks: int, output: str | None) -> None:
    if chunks <= 0:
        raise SystemExit("chunks must be positive")
    metrics = _simulate(chunks)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh)
    print(json.dumps(metrics))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=int, default=3, help="number of chunks")
    parser.add_argument("--output", type=str, help="optional metrics path")
    args = parser.parse_args()
    main(args.chunks, args.output)
