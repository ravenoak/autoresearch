"""Simulate API streaming guarantees with heartbeats and ordered chunks."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict


class StreamingMetrics(TypedDict):
    """Serialized metrics for the streaming simulation."""

    expected: int
    received: int
    heartbeats: int
    success: bool


def _write_metrics(path: Path, metrics: StreamingMetrics) -> None:
    """Persist metrics to ``path`` with deterministic formatting."""

    path.write_text(json.dumps(metrics, indent=2) + "\n")


def _stream(data: list[str], heartbeat_interval: int = 2) -> Iterator[str]:
    for i, item in enumerate(data):
        yield item
        if (i + 1) % heartbeat_interval == 0:
            yield "HEARTBEAT"
    yield "END"


def simulate() -> StreamingMetrics:
    """Stream chunks and verify order and heartbeat delivery."""
    data = ["alpha", "beta", "gamma"]
    received: list[str] = []
    heartbeats = 0
    for chunk in _stream(data):
        if chunk == "HEARTBEAT":
            heartbeats += 1
            continue
        if chunk == "END":
            break
        received.append(chunk)
    success = received == data and heartbeats >= 1
    metrics: StreamingMetrics = {
        "expected": len(data),
        "received": len(received),
        "heartbeats": heartbeats,
        "success": success,
    }
    out_path = Path(__file__).with_name("api_streaming_metrics.json")
    _write_metrics(out_path, metrics)
    return metrics


def run() -> StreamingMetrics:
    """Entry point for running the simulation."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
