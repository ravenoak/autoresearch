"""Estimate scheduler latency across worker counts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING


def latency_model(arrival_rate: float, service_rate: float, workers: int) -> float:
    """Approximate mean response time for an M/M/c queue."""
    if arrival_rate <= 0 or service_rate <= 0 or workers <= 0:
        raise ValueError("parameters must be positive")
    per_worker_arrival = arrival_rate / workers
    if per_worker_arrival >= service_rate:
        return float("inf")
    return 1.0 / (service_rate - per_worker_arrival)

if TYPE_CHECKING:
    from typing import Protocol

    class PlotAxes(Protocol):
        """Subset of matplotlib ``Axes`` used for plotting."""

        def plot(self, x: Sequence[float], y: Sequence[float], **kwargs: object) -> object:
            ...

        def xlabel(self, label: str) -> None:
            ...

        def ylabel(self, label: str) -> None:
            ...

        def title(self, label: str) -> None:
            ...

    class PlotFigure(Protocol):
        """Subset of matplotlib ``Figure`` used for persistence."""

        def savefig(self, fname: str | Path, **kwargs: object) -> None:
            ...


class _AxesWrapper:
    """Adapter exposing a stable plotting interface."""

    def __init__(self, axes: object) -> None:
        self._axes = axes

    def plot(self, x: Sequence[float], y: Sequence[float], **kwargs: object) -> object:
        plot = getattr(self._axes, "plot")
        return plot(x, y, **kwargs)

    def xlabel(self, label: str) -> None:
        setter = getattr(self._axes, "set_xlabel", None)
        if setter is not None:
            setter(label)
            return
        fallback = getattr(self._axes, "xlabel")
        fallback(label)

    def ylabel(self, label: str) -> None:
        setter = getattr(self._axes, "set_ylabel", None)
        if setter is not None:
            setter(label)
            return
        fallback = getattr(self._axes, "ylabel")
        fallback(label)

    def title(self, label: str) -> None:
        setter = getattr(self._axes, "set_title", None)
        if setter is not None:
            setter(label)
            return
        fallback = getattr(self._axes, "title")
        fallback(label)


class _FigureWrapper:
    """Adapter for figure persistence methods."""

    def __init__(self, figure: object) -> None:
        self._figure = figure

    def savefig(self, fname: str | Path, **kwargs: object) -> None:
        save = getattr(self._figure, "savefig")
        save(fname, **kwargs)

    def raw(self) -> object:
        """Return the underlying figure for cleanup."""

        return self._figure


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
        fig = _FigureWrapper(fig_obj)
        ax = _AxesWrapper(ax_obj)
        ax.plot(xs, ys, marker="o")
        ax.xlabel("workers")
        ax.ylabel("seconds")
        ax.title("Estimated latency")
        fig.savefig(out_dir / "agent_latency.svg", format="svg")
        plt.close(fig.raw())
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
