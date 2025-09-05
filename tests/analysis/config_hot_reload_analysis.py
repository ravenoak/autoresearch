"""Simulate configuration hot reload by updating a JSON file."""

from __future__ import annotations

import json
import time
from pathlib import Path


def simulate() -> dict[str, int | bool]:
    """Write, modify, and reload a config file to verify hot reload."""
    cfg_path = Path(__file__).with_name("temp_config.json")
    cfg_path.write_text(json.dumps({"value": 1}))
    original = json.loads(cfg_path.read_text())["value"]
    cfg_path.write_text(json.dumps({"value": 2}))
    time.sleep(0.01)
    reloaded = json.loads(cfg_path.read_text())["value"]
    cfg_path.unlink()
    success = original == 1 and reloaded == 2
    metrics = {"original": original, "reloaded": reloaded, "success": success}
    out_path = Path(__file__).with_name("config_hot_reload_metrics.json")
    out_path.write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


def run() -> dict[str, int | bool]:
    """Entry point for running the simulation."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
