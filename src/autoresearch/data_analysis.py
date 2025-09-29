"""Utilities for summarizing agent performance metrics.

This module exposes helpers for converting nested timing information into a
Polars :class:`~polars.DataFrame`. The ``polars`` dependency is optional; pass
``polars_enabled=True`` or set ``analysis.polars_enabled`` in the configuration
to activate it. When Polars is unavailable or disabled, ``metrics_dataframe``
raises :class:`RuntimeError`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, cast

from .config import ConfigLoader


class _PolarsDataFrame(Protocol):
    """Protocol representing the subset of :class:`polars.DataFrame` we rely on."""


class _PolarsNamespace(Protocol):
    """Protocol describing the attributes accessed on the ``polars`` module."""

    def DataFrame(self, data: Any) -> _PolarsDataFrame: ...


_polars: Any | None
try:  # pragma: no cover - optional dependency
    import polars as _polars
except Exception:  # pragma: no cover - optional dependency
    _polars = None

pl = cast(Optional[_PolarsNamespace], _polars)


def metrics_dataframe(
    metrics: Dict[str, Any], polars_enabled: Optional[bool] = None
) -> _PolarsDataFrame:
    """Return a Polars DataFrame summarizing agent timings."""
    cfg = ConfigLoader().config.analysis
    if polars_enabled is None:
        polars_enabled = cfg.polars_enabled
    if not polars_enabled or pl is None:
        raise RuntimeError("Polars analysis is disabled")

    assert pl is not None

    rows = []
    for agent, timings in metrics.get("agent_timings", {}).items():
        if timings:
            rows.append(
                {
                    "agent": agent,
                    "avg_time": sum(timings) / len(timings),
                    "count": len(timings),
                }
            )
    if not rows:
        return pl.DataFrame({"agent": [], "avg_time": [], "count": []})
    return pl.DataFrame(rows)
