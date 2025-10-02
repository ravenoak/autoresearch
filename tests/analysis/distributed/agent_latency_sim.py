"""Estimate scheduler latency across worker counts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast


class PlotAxes(Protocol):
    """Typed interface exposed to the rest of the module."""

    def plot(self, x: Sequence[float], y: Sequence[float], **kwargs: object) -> object:
        ...

    def xlabel(self, label: str) -> None:
        ...

    def ylabel(self, label: str) -> None:
        ...

    def title(self, label: str) -> None:
        ...


class PlotFigure(Protocol):
    """Typed wrapper interface for matplotlib ``Figure`` objects."""

    def savefig(self, fname: str | Path, **kwargs: object) -> None:
        ...

    def raw(self) -> object:
        ...


class _PyplotModule(Protocol):
    """Subset of ``matplotlib.pyplot`` relied upon by the simulation."""

    def subplots(self) -> tuple[object, object]:
        ...

    def close(self, figure: object) -> None:  # pragma: no cover - signature only
        ...


class _PlotCallable(Protocol):
    def __call__(self, x: Sequence[float], y: Sequence[float], **kwargs: object) -> object:
        ...


class _LabelCallable(Protocol):
    def __call__(self, label: str) -> None:
        ...


class _SavefigCallable(Protocol):
    def __call__(self, fname: str | Path, **kwargs: object) -> None:
        ...


def latency_model(arrival_rate: float, service_rate: float, workers: int) -> float:
    """Approximate mean response time for an M/M/c queue."""
    if arrival_rate <= 0 or service_rate <= 0 or workers <= 0:
        raise ValueError("parameters must be positive")
    per_worker_arrival = arrival_rate / workers
    if per_worker_arrival >= service_rate:
        return float("inf")
    return 1.0 / (service_rate - per_worker_arrival)


def _load_pyplot() -> _PyplotModule | None:
    """Return a minimal pyplot module if matplotlib is available."""

    if TYPE_CHECKING:
        return cast(_PyplotModule | None, object())
    try:  # pragma: no cover - optional dependency
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except Exception:  # pragma: no cover - optional dependency
        return None
    return cast(_PyplotModule, plt)


class _AxesWrapper(PlotAxes):
    """Adapter exposing a stable plotting interface."""

    def __init__(self, axes: object) -> None:
        self._axes = axes

    def plot(self, x: Sequence[float], y: Sequence[float], **kwargs: object) -> object:
        plot = cast(_PlotCallable, getattr(self._axes, "plot"))
        return plot(x, y, **kwargs)

    def xlabel(self, label: str) -> None:
        setter = getattr(self._axes, "set_xlabel", None)
        if setter is not None:
            cast(_LabelCallable, setter)(label)
            return
        fallback = getattr(self._axes, "xlabel", None)
        if fallback is not None:
            cast(_LabelCallable, fallback)(label)

    def ylabel(self, label: str) -> None:
        setter = getattr(self._axes, "set_ylabel", None)
        if setter is not None:
            cast(_LabelCallable, setter)(label)
            return
        fallback = getattr(self._axes, "ylabel", None)
        if fallback is not None:
            cast(_LabelCallable, fallback)(label)

    def title(self, label: str) -> None:
        setter = getattr(self._axes, "set_title", None)
        if setter is not None:
            cast(_LabelCallable, setter)(label)
            return
        fallback = getattr(self._axes, "title", None)
        if fallback is not None:
            cast(_LabelCallable, fallback)(label)


class _FigureWrapper(PlotFigure):
    """Adapter for figure persistence methods."""

    def __init__(self, figure: object) -> None:
        self._figure = figure

    def savefig(self, fname: str | Path, **kwargs: object) -> None:
        save = cast(_SavefigCallable, getattr(self._figure, "savefig"))
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
    pyplot = _load_pyplot()
    if pyplot is None:
        return results
    xs = sorted(results)
    ys = [results[w] for w in xs]
    fig_obj, ax_obj = pyplot.subplots()
    fig = _FigureWrapper(fig_obj)
    ax = _AxesWrapper(ax_obj)
    ax.plot(xs, ys, marker="o")
    ax.xlabel("workers")
    ax.ylabel("seconds")
    ax.title("Estimated latency")
    fig.savefig(out_dir / "agent_latency.svg", format="svg")
    pyplot.close(fig.raw())
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
