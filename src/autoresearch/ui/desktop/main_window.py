"""
Main window for the PySide6 Autoresearch desktop application.

This is the central component that provides the main interface for users
to interact with Autoresearch through a native desktop application.
"""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QProgressBar, QPushButton,
    QSplitter, QStatusBar, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
    QMessageBox
)

# Import desktop components first to avoid Qt-related issues
from .query_panel import QueryPanel
from .results_display import ResultsDisplay

try:
    # Import core Autoresearch components
    from ...orchestration import Orchestrator
    from ...config import ConfigLoader, ConfigModel
    from ...models import QueryResponse
    from ...output_format import OutputFormatter, OutputDepth
except ImportError:
    # For standalone testing/development
    Orchestrator = None
    ConfigLoader = None
    ConfigModel = None
    QueryResponse = None
    OutputFormatter = None
    OutputDepth = None


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

    def setup_status_bar(self) -> None:
        """Set up the status bar with real-time information."""
        status_bar = self.statusBar()

        # Left side: current status
        self.status_label = status_bar.findChild(type(self.progress_bar))
        if not self.status_label:
            from PySide6.QtWidgets import QLabel
            self.status_label = QLabel("Ready")
            status_bar.addWidget(self.status_label)

    def setup_connections(self) -> None:
        """Set up signal-slot connections."""
        if self.query_panel:
            self.query_panel.query_submitted.connect(self.on_query_submitted)

    def load_configuration(self) -> None:
        """Load Autoresearch configuration."""
        try:
            if ConfigLoader:
                self.config_loader = ConfigLoader()
                self.config = self.config_loader.load_config()

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

        self.status_label.setText("Query completed")

        # Update window title with query summary
        query_preview = self.current_query[:50] + "..." if len(self.current_query) > 50 else self.current_query
        self.setWindowTitle(f"Autoresearch - {query_preview}")

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
