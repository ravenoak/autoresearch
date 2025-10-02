"""Simulate configuration hot reload by updating a JSON file."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TypedDict


class ConfigState(TypedDict):
    """Serialized configuration payload."""

    value: int


class HotReloadMetrics(TypedDict):
    """Metrics captured during the hot reload simulation."""

    original: int
    reloaded: int
    success: bool


def _load_value(path: Path) -> int:
    """Read the ``value`` field from ``path`` enforcing the expected schema."""

    payload = json.loads(path.read_text())
    state = ConfigState(value=int(payload["value"]))
    return state["value"]


def _write_metrics(path: Path, metrics: HotReloadMetrics) -> None:
    """Persist metrics to ``path`` with deterministic formatting."""

    path.write_text(json.dumps(metrics, indent=2) + "\n")


def simulate() -> HotReloadMetrics:
    """Write, modify, and reload a config file to verify hot reload."""

    cfg_path = Path(__file__).with_name("temp_config.json")
    cfg_path.write_text(json.dumps({"value": 1}))
    original = _load_value(cfg_path)
    cfg_path.write_text(json.dumps({"value": 2}))
    time.sleep(0.01)
    reloaded = _load_value(cfg_path)
    cfg_path.unlink()
    success = original == 1 and reloaded == 2
    metrics: HotReloadMetrics = {
        "original": original,
        "reloaded": reloaded,
        "success": success,
    }
    out_path = Path(__file__).with_name("config_hot_reload_metrics.json")
    _write_metrics(out_path, metrics)
    return metrics


def run() -> HotReloadMetrics:
    """Entry point for running the simulation."""

    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
