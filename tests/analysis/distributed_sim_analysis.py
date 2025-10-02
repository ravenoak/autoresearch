"""Analyze message throughput scaling for the distributed simulation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

from scripts import distributed_sim


class SimulationMetrics(TypedDict):
    """Aggregated metrics for a single worker count."""

    throughput: float
    cpu_percent: float
    memory_mb: float


if TYPE_CHECKING:
    from collections.abc import Sequence

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

    class _PyplotModule(Protocol):
        def subplots(self) -> tuple[Figure, Axes]:
            ...

        def close(self, figure: Figure) -> None:
            ...


def _load_pyplot() -> "_PyplotModule | None":
    """Return a typed matplotlib module when available."""

    if TYPE_CHECKING:
        return cast("_PyplotModule | None", object())
    try:  # pragma: no cover - optional dependency
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except Exception:  # pragma: no cover - optional dependency
        return None
    if not hasattr(plt, "subplots") or not hasattr(plt, "close"):
        return None
    return cast("_PyplotModule", plt)


def _write_metrics(path: Path, metrics: dict[int, SimulationMetrics]) -> None:
    """Persist ``metrics`` to ``path`` with canonical formatting."""

    path.write_text(json.dumps(metrics, indent=2) + "\n")


def run() -> dict[int, SimulationMetrics]:
    """Run simulations for multiple worker counts and store metrics."""

    results: dict[int, SimulationMetrics] = {}
    for workers in (1, 2, 4):
        samples = [
            distributed_sim.run_simulation(workers=workers, messages=100, loops=5)
            for _ in range(3)
        ]
        results[workers] = {
            "throughput": sum(sample["throughput"] for sample in samples) / len(samples),
            "cpu_percent": sum(sample["cpu_percent"] for sample in samples) / len(samples),
            "memory_mb": sum(sample["memory_mb"] for sample in samples) / len(samples),
        }
    out_dir = Path(__file__).resolve().parent
    _write_metrics(out_dir.joinpath("distributed_sim_metrics.json"), results)

    pyplot = _load_pyplot()
    if pyplot is not None:
        xs = sorted(results)
        ys = [results[w]["throughput"] for w in xs]
        fig, ax = pyplot.subplots()
        ax.plot(xs, ys, marker="o")
        ax.set_xlabel("workers")
        ax.set_ylabel("messages/sec")
        ax.set_title("Message throughput scaling")
        fig.savefig(out_dir / "distributed_sim_plot.png")
        pyplot.close(fig)
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
