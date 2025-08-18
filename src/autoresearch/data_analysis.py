"""Utilities for summarizing agent performance metrics.

This module exposes helpers for converting nested timing information into a
Polars :class:`~polars.DataFrame`. The ``polars`` dependency is optional; pass
``polars_enabled=True`` or set ``analysis.polars_enabled`` in the configuration
to activate it. When Polars is unavailable or disabled, ``metrics_dataframe``
raises :class:`RuntimeError`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import polars as pl
except Exception:  # pragma: no cover - optional dependency
    pl = None  # type: ignore

from .config import ConfigLoader


def metrics_dataframe(
    metrics: Dict[str, Any], polars_enabled: Optional[bool] = None
) -> "pl.DataFrame":
    """Return a Polars DataFrame summarizing agent timings."""
    cfg = ConfigLoader().config.analysis
    if polars_enabled is None:
        polars_enabled = cfg.polars_enabled
    if not polars_enabled or pl is None:
        raise RuntimeError("Polars analysis is disabled")

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
