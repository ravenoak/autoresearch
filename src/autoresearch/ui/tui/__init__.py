"""Textual dashboard integration for the Autoresearch CLI."""

from __future__ import annotations

from .dashboard import DashboardApp, DashboardUnavailableError, run_dashboard

__all__ = [
    "DashboardApp",
    "DashboardUnavailableError",
    "run_dashboard",
]
