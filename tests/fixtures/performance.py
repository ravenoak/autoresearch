# mypy: ignore-errors
"""Performance-related fixtures that expose recorded benchmark baselines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from tests.typing_helpers import TypedFixture


_BASELINE_DIR = Path(__file__).resolve().parents[2] / "baseline" / "evaluation"


def _load_baseline(name: str) -> Mapping[str, Any]:
    baseline_path = _BASELINE_DIR / name
    with baseline_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data


@pytest.fixture(scope="session")
def scheduler_benchmark_baseline() -> TypedFixture[Mapping[str, Any]]:
    """Return scheduler benchmark metrics recorded in the repository baseline."""

    return _load_baseline("scheduler_benchmark.json")


@pytest.fixture(scope="session")
def distributed_orchestrator_baseline() -> TypedFixture[Mapping[str, Any]]:
    """Return distributed orchestrator metrics recorded in the baseline suite."""

    return _load_baseline("orchestrator_distributed_sim.json")

