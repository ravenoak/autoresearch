"""
PySide6 Desktop Interface for Autoresearch.

This package provides a professional, native desktop GUI for Autoresearch
using PySide6 (Qt for Python) instead of web-based Streamlit.

The desktop interface provides:
- Native performance with GPU acceleration
- Multi-window support for comparing queries
- Rich interactions (drag-and-drop, annotations, keyboard shortcuts)
- Professional appearance matching research tools
- Offline-first operation (no server required)
"""

from __future__ import annotations

import os

# Default to headless-friendly Qt settings so CI and automated tests run
# without a display server while still allowing callers to override them.
for key, value in (
    ("QT_QPA_PLATFORM", "offscreen"),
    ("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu --disable-software-rasterizer"),
    ("QTWEBENGINE_DISABLE_SANDBOX", "1"),
    ("AUTORESEARCH_SUPPRESS_DIALOGS", "1"),
):
    os.environ.setdefault(key, value)

from . import main  # noqa: E402
from .config_editor import ConfigEditor  # noqa: E402
from .export_manager import ExportManager  # noqa: E402
from .knowledge_graph_view import KnowledgeGraphView  # noqa: E402
from .main_window import AutoresearchMainWindow  # noqa: E402
from .metrics_dashboard import MetricsDashboard  # noqa: E402
from .results_table import SearchResultsModel, SearchResultsTableView  # noqa: E402
from .session_manager import SessionManager  # noqa: E402

__version__ = "0.1.0"
__all__ = [
    "main",
    "AutoresearchMainWindow",
    "ConfigEditor",
    "ExportManager",
    "KnowledgeGraphView",
    "MetricsDashboard",
    "SearchResultsModel",
    "SearchResultsTableView",
    "SessionManager",
]
