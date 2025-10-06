# mypy: ignore-errors
from __future__ import annotations

from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Protocol, TypedDict, cast


class Metrics(TypedDict):
    """Predicted or measured throughput and latency."""

    throughput: float
    latency_s: float


class WorkerComparison(TypedDict):
    """Comparison entry for a worker count."""

    workers: float
    predicted: Metrics
    measured: Metrics


class DistributedPerfCompareModule(Protocol):
    """Subset of the compare script used in tests."""

    def compare(
        self,
        max_workers: int,
        arrival_rate: float,
        service_rate: float,
        tasks: int,
        network_delay: float = ...,
        seed: int | None = ...,
    ) -> list[WorkerComparison]:
        ...


def _load_module() -> DistributedPerfCompareModule:
    path = Path(__file__).resolve().parents[2] / "scripts" / "distributed_perf_compare.py"
    spec: ModuleSpec | None = spec_from_file_location("distributed_perf_compare", path)
    if spec is None or spec.loader is None:
        raise ImportError("distributed_perf_compare")
    module: ModuleType = module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(DistributedPerfCompareModule, module)


def test_compare_matches_theory_within_tolerance() -> None:
    mod = _load_module()
    results: list[WorkerComparison] = mod.compare(
        max_workers=2,
        arrival_rate=80,
        service_rate=100,
        tasks=200,
        network_delay=0.0,
        seed=42,
    )
    for entry in results:
        pred = entry["predicted"]
        meas = entry["measured"]
        assert abs(pred["throughput"] - meas["throughput"]) / pred["throughput"] < 0.3
        assert abs(pred["latency_s"] - meas["latency_s"]) / pred["latency_s"] < 0.3
