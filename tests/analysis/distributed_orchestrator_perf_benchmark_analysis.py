"""Run distributed orchestrator benchmark and persist metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

from scripts import distributed_orchestrator_perf_benchmark as bench


class WorkerMetrics(TypedDict):
    """Benchmark metrics captured for a worker count."""

    avg_latency_s: float
    throughput: float
    memory_mb: float


if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Protocol

    class Axes(Protocol):
        """Subset of matplotlib ``Axes`` used for plotting."""

        def plot(self, x: Sequence[float], y: Sequence[float], **kwargs: object) -> object:
            ...

        def set_xlabel(self, label: str) -> None:
            ...

        def set_ylabel(self, label: str) -> None:
            ...

        def set_title(self, label: str) -> None:
            ...

    class Figure(Protocol):
        """Subset of matplotlib ``Figure`` used for persistence."""

        def savefig(self, fname: str | Path, **kwargs: object) -> None:
            ...


def run() -> dict[int, WorkerMetrics]:
    """Execute benchmark for select worker counts and store metrics."""
    raw = bench.run_benchmark(max_workers=4, tasks=50, network_latency=0.005)
    results: dict[int, WorkerMetrics] = {}
    for item in raw:
        workers = int(item["workers"])
        if workers in (1, 2, 4):
            results[workers] = {
                "avg_latency_s": item["avg_latency_s"],
                "throughput": item["throughput"],
                "memory_mb": item["memory_mb"],
            }
    out_dir = Path(__file__).resolve().parent
    out_dir.joinpath("distributed_orchestrator_perf_benchmark_metrics.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    try:  # optional visualization
        from matplotlib import pyplot as plt

        xs = sorted(results)
        ys = [results[w]["throughput"] for w in xs]
        fig_obj, ax_obj = plt.subplots()
        fig = cast("Figure", fig_obj)
        ax = cast("Axes", ax_obj)
        ax.plot(xs, ys, marker="o")
        ax.set_xlabel("workers")
        ax.set_ylabel("tasks/sec")
        ax.set_title("Orchestrator throughput scaling")
        fig.savefig(out_dir / "distributed_orchestrator_perf_benchmark_plot.png")
        plt.close(fig)
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
