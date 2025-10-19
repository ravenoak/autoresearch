"""
Main window for the PySide6 Autoresearch desktop application.

This is the central component that provides the main interface for users
to interact with Autoresearch through a native desktop application.
"""

from __future__ import annotations

import sys
import uuid
from typing import Any, Mapping, Optional

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QProgressBar,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

# Import desktop components first to avoid Qt-related issues
from .query_panel import QueryPanel
from .results_display import ResultsDisplay
from .config_editor import ConfigEditor
from .session_manager import SessionManager
from .export_manager import ExportManager

try:
    # Import core Autoresearch components
    from ...orchestration import Orchestrator
    from ...config import ConfigLoader, ConfigModel
    from ...models import QueryResponse
    from ...output_format import OutputFormatter, OutputDepth
    from ...storage import StorageManager
except ImportError:
    # For standalone testing/development
    Orchestrator = None
    ConfigLoader = None
    ConfigModel = None
    QueryResponse = None
    OutputFormatter = None
    OutputDepth = None
    StorageManager = None


class AutoresearchMainWindow(QMainWindow):
    """
    Main window for the Autoresearch desktop application.

    Provides a professional, multi-pane interface for research queries
    with real-time progress indicators and comprehensive results display.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        self.orchestrator: Optional[Orchestrator] = None
        self.config_loader: Optional[ConfigLoader] = None
        self.config: Optional[ConfigModel] = None

        # UI components
        self.query_panel: Optional[QueryPanel] = None
        self.results_display: Optional[ResultsDisplay] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.config_editor: Optional[ConfigEditor] = None
        self.session_manager: Optional[SessionManager] = None
        self.export_manager: Optional[ExportManager] = None
        self.config_dock: Optional[QDockWidget] = None
        self.session_dock: Optional[QDockWidget] = None
        self.export_dock: Optional[QDockWidget] = None

        # Query execution state
        self.current_query: str = ""
        self.is_query_running: bool = False

        self.setup_ui()
        self.setup_connections()
        self.load_configuration()

    def setup_ui(self) -> None:
        """Set up the main window user interface."""
        self.setWindowTitle("Autoresearch - AI Research Assistant")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)

        # Query panel (top)
        self.query_panel = QueryPanel()
        splitter.addWidget(self.query_panel)

        # Results display (bottom, expandable)
        self.results_display = ResultsDisplay()
        splitter.addWidget(self.results_display)

        # Set splitter proportions (query panel smaller, results larger)
        splitter.setSizes([200, 600])

        layout.addWidget(splitter)

        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

        # Set up status bar
        self.setup_status_bar()
        self.setup_dock_widgets()

    def setup_status_bar(self) -> None:
        """Set up the status bar with real-time information."""
        status_bar = self.statusBar()

        # Left side: current status
        self.status_label = status_bar.findChild(type(self.progress_bar))
        if not self.status_label:
            from PySide6.QtWidgets import QLabel
            self.status_label = QLabel("Ready")
            status_bar.addWidget(self.status_label)

    def setup_dock_widgets(self) -> None:
        """Create dock widgets for configuration, sessions, and exports."""

        self.config_editor = ConfigEditor()
        self.config_dock = QDockWidget("Configuration", self)
        self.config_dock.setObjectName("ConfigurationDock")
        self.config_dock.setWidget(self.config_editor)
        self.config_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.config_dock)

        self.session_manager = SessionManager()
        self.session_dock = QDockWidget("Sessions", self)
        self.session_dock.setObjectName("SessionsDock")
        self.session_dock.setWidget(self.session_manager)
        self.session_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.session_dock)
        if self.config_dock:
            self.tabifyDockWidget(self.config_dock, self.session_dock)

        self.export_manager = ExportManager()
        self.export_dock = QDockWidget("Exports", self)
        self.export_dock.setObjectName("ExportsDock")
        self.export_dock.setWidget(self.export_manager)
        self.export_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.export_dock)

    def setup_connections(self) -> None:
        """Set up signal-slot connections."""
        if self.query_panel:
            self.query_panel.query_submitted.connect(self.on_query_submitted)
        if self.config_editor:
            self.config_editor.configuration_changed.connect(self.on_configuration_changed)
        if self.session_manager:
            self.session_manager.session_selected.connect(self.on_session_selected)
            self.session_manager.new_session_requested.connect(self.on_new_session_requested)
        if self.export_manager:
            self.export_manager.export_requested.connect(self.on_export_requested)

    def load_configuration(self) -> None:
        """Load Autoresearch configuration."""
        try:
            if ConfigLoader:
                self.config_loader = ConfigLoader()
                self.config = self.config_loader.load_config()
                if self.config_editor:
                    self.config_editor.load_config(self.config)

            if Orchestrator:
                self.orchestrator = Orchestrator()

            self.status_label.setText("Configuration loaded - Ready for queries")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Configuration Error",
                f"Failed to load configuration: {e}\n\nSome features may not work correctly."
            )
            self.status_label.setText("Configuration error - Limited functionality")

    def on_configuration_changed(self, updated_config: dict[str, Any]) -> None:
        """Handle configuration changes from the dock widget."""

        try:
            self.config = self._build_config_model(updated_config)
            self.status_label.setText("Configuration updated - ready to run queries")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Configuration",
                f"Failed to apply configuration changes: {exc}",
            )

    def _build_config_model(self, data: Mapping[str, Any]) -> Any:
        if not ConfigModel:
            return data

        if hasattr(ConfigModel, "model_validate"):
            return ConfigModel.model_validate(data)
        if hasattr(ConfigModel, "parse_obj"):
            return ConfigModel.parse_obj(data)

        return ConfigModel(**data)

    def on_session_selected(self, session_id: str) -> None:
        """Update status when a session is activated."""

        self.status_label.setText(f"Session activated: {session_id}")

    def on_new_session_requested(self) -> None:
        """Reset the query panel to start a fresh session."""

        if self.query_panel:
            self.query_panel.clear_query()
        self.current_query = ""
        self.status_label.setText("New session ready")

    def on_export_requested(self, export_id: str) -> None:
        """Trigger an export action via the storage manager."""

        if not StorageManager:
            QMessageBox.information(
                self,
                "Exports Unavailable",
                "Export functionality is unavailable in this environment.",
            )
            return

        try:
            if export_id.lower().endswith("graphml"):
                StorageManager.export_knowledge_graph_graphml()
            elif "json" in export_id.lower():
                StorageManager.export_knowledge_graph_json()
            else:
                QMessageBox.information(
                    self,
                    "Export",
                    f"No handler registered for export '{export_id}'.",
                )
                return
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export data: {exc}",
            )
            return

        QMessageBox.information(
            self,
            "Export Started",
            f"Export '{export_id}' triggered. Check the configured output directory.",
        )

    @Slot(str)
    def on_query_submitted(self, query: str) -> None:
        """Handle query submission from the query panel."""
        if not query.strip():
            QMessageBox.warning(self, "Empty Query", "Please enter a query before submitting.")
            return

        if self.is_query_running:
            QMessageBox.information(
                self, "Query in Progress",
                "A query is already running. Please wait for it to complete."
            )
            return

        self.current_query = query
        self.run_query()

    def run_query(self) -> None:
        """Execute the current query."""
        if not self.orchestrator or not self.config:
            QMessageBox.critical(
                self, "System Error",
                "Autoresearch core components are not available. Please check your installation."
            )
            return

        self.is_query_running = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Running query...")

        # Run query in separate thread to keep UI responsive
        from PySide6.QtCore import QThread, QThreadPool, QRunnable, QTimer

        class QueryWorker(QRunnable):
            def __init__(self, orchestrator, query, config, parent):
                super().__init__()
                self.orchestrator = orchestrator
                self.query = query
                self.config = config
                self.parent = parent

            def run(self):
                try:
                    # Execute the query
                    result = self.orchestrator.run_query(self.query, self.config)

                    # Update UI on main thread
                    QTimer.singleShot(0, lambda: self.parent.display_results(result))

                except Exception as e:
                    QTimer.singleShot(0, lambda: self.parent.display_error(e))

        # Start the query worker
        worker = QueryWorker(self.orchestrator, self.current_query, self.config, self)
        QThreadPool.globalInstance().start(worker)

    def display_results(self, result: QueryResponse) -> None:
        """Display query results in the results panel."""
        self.is_query_running = False
        self.progress_bar.setVisible(False)

        if self.results_display:
            self.results_display.display_results(result)

        self.update_export_options(result)

        session_title = self.current_query.strip() or "Untitled Query"
        if len(session_title) > 50:
            window_title = f"{session_title[:50]}..."
        else:
            window_title = session_title

        if self.session_manager:
            self.session_manager.add_session(uuid.uuid4().hex, session_title)

        self.status_label.setText("Query completed")

        self.setWindowTitle(f"Autoresearch - {window_title}")

    def update_export_options(self, result: QueryResponse) -> None:
        """Update export availability based on the latest result."""

        if not self.export_manager:
            return

        exports: dict[str, bool] = {}
        metrics = getattr(result, "metrics", None)
        if isinstance(metrics, Mapping):
            knowledge_metrics = metrics.get("knowledge_graph")
            if isinstance(knowledge_metrics, Mapping):
                export_info = knowledge_metrics.get("exports")
                if isinstance(export_info, Mapping):
                    exports = {str(key): bool(value) for key, value in export_info.items()}

        self.export_manager.set_available_exports(exports)

    def display_error(self, error: Exception) -> None:
        """Display query error to the user."""
        self.is_query_running = False
        self.progress_bar.setVisible(False)

        error_msg = str(error)
        QMessageBox.critical(
            self, "Query Error",
            f"An error occurred while running your query:\n\n{error_msg}"
        )

        self.status_label.setText("Query failed")

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Clean up any running queries
        if self.is_query_running:
            reply = QMessageBox.question(
                self, "Confirm Close",
                "A query is currently running. Do you want to close anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

        event.accept()
