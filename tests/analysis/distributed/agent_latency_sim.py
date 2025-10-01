"""Estimate scheduler latency across worker counts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast


def latency_model(arrival_rate: float, service_rate: float, workers: int) -> float:
    """Approximate mean response time for an M/M/c queue."""
    if arrival_rate <= 0 or service_rate <= 0 or workers <= 0:
        raise ValueError("parameters must be positive")
    per_worker_arrival = arrival_rate / workers
    if per_worker_arrival >= service_rate:
        return float("inf")
    return 1.0 / (service_rate - per_worker_arrival)

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


def run(arrival_rate: float = 5.0, service_rate: float = 2.0) -> dict[int, float]:
    """Compute latency for varying worker counts and optionally plot results."""
    results: dict[int, float] = {}
    for workers in (1, 2, 4, 8):
        results[workers] = latency_model(arrival_rate, service_rate, workers)
    out_dir = Path(__file__).resolve().parent
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        xs = sorted(results)
        ys = [results[w] for w in xs]
        fig_obj, ax_obj = plt.subplots()
        fig = cast("Figure", fig_obj)
        ax = cast("Axes", ax_obj)
        ax.plot(xs, ys, marker="o")
        ax.set_xlabel("workers")
        ax.set_ylabel("seconds")
        ax.set_title("Estimated latency")
        fig.savefig(out_dir / "agent_latency.svg", format="svg")
        plt.close(fig)
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
