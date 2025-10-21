"""
Main window for the PySide6 Autoresearch desktop application.

This is the central component that provides the main interface for users
to interact with Autoresearch through a native desktop application.
"""

from __future__ import annotations

import os
import sys
import uuid
from enum import Enum
from time import monotonic
from typing import Any, Mapping, Optional

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QProgressBar,
    QHBoxLayout,
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
from .telemetry import telemetry

try:
    # Import core Autoresearch components
    from ...orchestration import Orchestrator, ReasoningMode
    from ...config import ConfigLoader, ConfigModel
    from ...models import QueryResponse
    from ...output_format import OutputFormatter, OutputDepth
    from ...storage import StorageManager
    from ...orchestration.metrics import get_orchestration_metrics
except ImportError:
    # For standalone testing/development
    Orchestrator = None
    ReasoningMode = None
    ConfigLoader = None
    ConfigModel = None
    QueryResponse = None
    OutputFormatter = None
    OutputDepth = None
    StorageManager = None
    get_orchestration_metrics = None


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

        self._metrics_provider = (
            get_orchestration_metrics if callable(get_orchestration_metrics) else None
        )
        self._latest_metrics_payload: Mapping[str, Any] | None = None
        self._status_message: str = "Ready"
        self._metric_labels: dict[str, QLabel] = {}
        self._menu_actions: list[QAction] = []
        self.metrics_timer: Optional[QTimer] = None

        # Query execution state
        self.current_query: str = ""
        self.is_query_running: bool = False
        self._active_session_id: Optional[str] = None
        self._cancelled_session_ids: set[str] = set()
        self._query_started_at: Optional[float] = None
        self._active_worker: Any = None

        self.setup_ui()
        self.setup_menu_bar()
        self.setup_connections()
        self._start_metrics_timer()
        self.load_configuration()

    def _suppress_dialogs(self) -> bool:
        """Return True when UI dialogs should be suppressed (e.g., automated tests)."""

        flag = os.environ.get("AUTORESEARCH_SUPPRESS_DIALOGS", "")
        return flag.lower() in {"1", "true", "yes", "on"}

    def _log_dialog(self, level: str, title: str, message: str) -> None:
        """Record dialog content when suppression is enabled."""

        print(f"[{level.upper()}] {title}: {message}", file=sys.stderr)

    def _show_information(self, title: str, message: str) -> None:
        if self._suppress_dialogs():
            self._log_dialog("info", title, message)
            return
        QMessageBox.information(self, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        if self._suppress_dialogs():
            self._log_dialog("warning", title, message)
            return
        QMessageBox.warning(self, title, message)

    def _show_critical(self, title: str, message: str) -> None:
        if self._suppress_dialogs():
            self._log_dialog("critical", title, message)
            return
        QMessageBox.critical(self, title, message)

    def _ask_question(self, title: str, message: str, buttons: Any, default: Any) -> Any:
        if self._suppress_dialogs():
            self._log_dialog("question", title, message)
            return default
        return QMessageBox.question(self, title, message, buttons, default)

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
        self.setup_status_bar()
        self.setup_dock_widgets()

    def setup_status_bar(self) -> None:
        """Set up the status bar with real-time information."""
        status_bar = self.statusBar()
        status_bar.setObjectName("main-status-bar")

        metrics_container = QWidget()
        metrics_layout = QHBoxLayout(metrics_container)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(12)

        metric_defaults = {
            "cpu": "CPU: --%",
            "memory": "Memory: -- MB",
            "tokens": "Tokens: --",
        }
        for key, label_text in metric_defaults.items():
            label = QLabel(label_text)
            label.setObjectName(f"status-metric-{key}")
            metrics_layout.addWidget(label)
            self._metric_labels[key] = label

        metrics_layout.addStretch(1)
        status_bar.addPermanentWidget(metrics_container)

        if self.progress_bar:
            status_bar.addPermanentWidget(self.progress_bar)

        self._set_status_message(self._status_message)
        self._refresh_status_metrics()

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
            self.query_panel.query_cancelled.connect(self.on_query_cancelled)
        if self.config_editor:
            self.config_editor.configuration_changed.connect(self.on_configuration_changed)
        if self.session_manager:
            self.session_manager.session_selected.connect(self.on_session_selected)
            self.session_manager.new_session_requested.connect(self.on_new_session_requested)
        if self.export_manager:
            self.export_manager.export_requested.connect(self.on_export_requested)

    def setup_menu_bar(self) -> None:
        """Configure the main menu bar with standard desktop actions."""

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)
        menu_bar.clear()

        file_menu = menu_bar.addMenu("&File")
        new_session_action = QAction("&New Session", self)
        new_session_action.setShortcut(QKeySequence.New)
        new_session_action.triggered.connect(self.on_new_session_requested)
        file_menu.addAction(new_session_action)
        self._register_action(new_session_action)

        export_action = QAction("E&xport Results…", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._trigger_export_action)
        file_menu.addAction(export_action)
        self._register_action(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self._register_action(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(lambda: self._invoke_query_text_method("undo"))
        edit_menu.addAction(undo_action)
        self._register_action(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(lambda: self._invoke_query_text_method("redo"))
        edit_menu.addAction(redo_action)
        self._register_action(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(lambda: self._invoke_query_text_method("cut"))
        edit_menu.addAction(cut_action)
        self._register_action(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(lambda: self._invoke_query_text_method("copy"))
        edit_menu.addAction(copy_action)
        self._register_action(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(lambda: self._invoke_query_text_method("paste"))
        edit_menu.addAction(paste_action)
        self._register_action(paste_action)

        view_menu = menu_bar.addMenu("&View")
        if self.config_dock:
            config_action = self.config_dock.toggleViewAction()
            config_action.setShortcut(QKeySequence("Ctrl+1"))
            view_menu.addAction(config_action)
            self._register_action(config_action)
        if self.session_dock:
            session_action = self.session_dock.toggleViewAction()
            session_action.setShortcut(QKeySequence("Ctrl+2"))
            view_menu.addAction(session_action)
            self._register_action(session_action)
        if self.export_dock:
            export_dock_action = self.export_dock.toggleViewAction()
            export_dock_action.setShortcut(QKeySequence("Ctrl+3"))
            view_menu.addAction(export_dock_action)
            self._register_action(export_dock_action)

        help_menu = menu_bar.addMenu("&Help")
        help_action = QAction("&View Documentation", self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self._open_help_center)
        help_menu.addAction(help_action)
        self._register_action(help_action)

        about_action = QAction("&About Autoresearch", self)
        about_action.setShortcut(QKeySequence("Shift+F1"))
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        self._register_action(about_action)

    def _register_action(self, action: QAction) -> None:
        """Retain references to actions to prevent premature garbage collection."""

        self._menu_actions.append(action)

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

            self._set_status_message("Configuration loaded - ready for queries")
        except Exception as e:
            self._show_warning(
                "Configuration Error",
                f"Failed to load configuration: {e}\n\nSome features may not work correctly."
            )
            self._set_status_message("Configuration error - limited functionality")

    def on_configuration_changed(self, updated_config: dict[str, Any]) -> None:
        """Handle configuration changes from the dock widget."""

        try:
            self.config = self._build_config_model(updated_config)
            self._set_status_message("Configuration updated - ready to run queries")
        except Exception as exc:
            self._show_warning(
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

    def _merge_query_panel_configuration(self) -> None:
        """Synchronise query panel overrides with the active configuration."""

        if not self.query_panel or not self.config:
            return

        overrides = self.query_panel.get_configuration()
        if not overrides:
            return

        self._apply_configuration_overrides(overrides)

    def _apply_configuration_overrides(self, overrides: Mapping[str, Any]) -> None:
        """Apply configuration overrides and refresh dependent views."""

        if not overrides or not self.config:
            return

        updates = dict(overrides)
        reasoning_mode = updates.get("reasoning_mode")
        if reasoning_mode is not None:
            updates["reasoning_mode"] = self._coerce_reasoning_mode(reasoning_mode)

        if hasattr(self.config, "model_copy"):
            self.config = self.config.model_copy(update=updates)  # type: ignore[assignment]
        elif isinstance(self.config, Mapping):
            self.config = {**self.config, **updates}
        else:
            for key, value in updates.items():
                setattr(self.config, key, value)

        if self.config_editor:
            self.config_editor.load_config(self.config)

    def _coerce_reasoning_mode(self, value: Any) -> Any:
        """Normalise reasoning mode overrides for ConfigModel compatibility."""

        if value is None:
            return value

        if ReasoningMode and isinstance(value, str):
            try:
                return ReasoningMode(value)
            except ValueError:
                pass

        current_mode = getattr(self.config, "reasoning_mode", None)
        if isinstance(current_mode, Enum):
            try:
                return type(current_mode)(value)
            except ValueError:
                return current_mode

        return value

    def on_session_selected(self, session_id: str) -> None:
        """Update status when a session is activated."""

        self._set_status_message(f"Session activated: {session_id}")

    def on_new_session_requested(self) -> None:
        """Reset the query panel to start a fresh session."""

        if self.query_panel:
            self.query_panel.clear_query()
        self.current_query = ""
        self._latest_metrics_payload = None
        self._refresh_status_metrics()
        self._set_status_message("New session ready")

    def on_export_requested(self, export_id: str) -> None:
        """Trigger an export action via the storage manager."""

        if not StorageManager:
            self._show_information(
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
                self._show_information(
                    "Export",
                    f"No handler registered for export '{export_id}'.",
                )
                return
        except Exception as exc:
            self._show_warning(
                "Export Failed",
                f"Failed to export data: {exc}",
            )
            return

        self._show_information(
            "Export Started",
            f"Export '{export_id}' triggered. Check the configured output directory.",
        )

    @Slot(str)
    def on_query_submitted(self, query: str) -> None:
        """Handle query submission from the query panel."""
        if not query.strip():
            self._show_warning("Empty Query", "Please enter a query before submitting.")
            return

        if self.is_query_running:
            self._show_information(
                "Query in Progress",
                "A query is already running. Please wait for it to complete."
            )
            return

        self.current_query = query
        self._query_started_at = monotonic()
        session_id = self._resolve_session_id()
        self._active_session_id = session_id
        self._cancelled_session_ids.discard(session_id)
        self.run_query()

    def run_query(self) -> None:
        """Execute the current query."""
        if not self.orchestrator or not self.config:
            self._show_critical(
                "System Error",
                "Autoresearch core components are not available. Please check your installation."
            )
            return

        self._merge_query_panel_configuration()

        if self.query_panel:
            self.query_panel.set_busy(True)

        self.is_query_running = True
        if self._active_session_id is None:
            self._active_session_id = self._resolve_session_id()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self._set_status_message("Running query…")
        self._latest_metrics_payload = None
        self._refresh_status_metrics()

        # Run query in separate thread to keep UI responsive
        from PySide6.QtCore import QThread, QThreadPool, QRunnable, QTimer

        class QueryWorker(QRunnable):
            def __init__(self, orchestrator, query, config, parent, session_id):
                super().__init__()
                self.orchestrator = orchestrator
                self.query = query
                self.config = config
                self.parent = parent
                self.session_id = session_id

            def run(self):
                try:
                    # Execute the query
                    result = self.orchestrator.run_query(self.query, self.config)

                    # Update UI on main thread
                    QTimer.singleShot(
                        0,
                        lambda: self.parent.display_results(result, self.session_id),
                    )

                except Exception as e:
                    QTimer.singleShot(
                        0,
                        lambda: self.parent.display_error(e, self.session_id),
                    )

        # Start the query worker
        worker = QueryWorker(
            self.orchestrator,
            self.current_query,
            self.config,
            self,
            self._active_session_id,
        )
        QThreadPool.globalInstance().start(worker)
        self._active_worker = worker

    def display_results(
        self, result: QueryResponse, session_id: Optional[str] = None
    ) -> None:
        """Display query results in the results panel."""
        if session_id and session_id in self._cancelled_session_ids:
            self._cancelled_session_ids.discard(session_id)
            return

        self.is_query_running = False
        self.progress_bar.setVisible(False)

        if self.query_panel:
            self.query_panel.set_busy(False)
            self.query_panel.clear_session_context()

        if self.results_display:
            self.results_display.display_results(result)

        self.update_export_options(result)

        metrics_payload = getattr(result, "metrics", None)
        if isinstance(metrics_payload, Mapping):
            self._latest_metrics_payload = metrics_payload
        else:
            self._latest_metrics_payload = None
        self._refresh_status_metrics()

        session_title = self.current_query.strip() or "Untitled Query"
        if len(session_title) > 50:
            window_title = f"{session_title[:50]}..."
        else:
            window_title = session_title

        if self.session_manager:
            self.session_manager.add_session(uuid.uuid4().hex, session_title)

        self._set_status_message("Query completed")

        self.setWindowTitle(f"Autoresearch - {window_title}")

        payload = self._build_query_payload(
            session_id or self._active_session_id,
            status="completed",
            extra={"result_has_metrics": bool(self._latest_metrics_payload)},
        )
        telemetry.emit("ui.query.completed", payload)
        self._finalise_session_state()

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

    def display_error(self, error: Exception, session_id: Optional[str] = None) -> None:
        """Display query error to the user."""
        if session_id and session_id in self._cancelled_session_ids:
            self._cancelled_session_ids.discard(session_id)
            return

        self.is_query_running = False
        self.progress_bar.setVisible(False)

        if self.query_panel:
            self.query_panel.set_busy(False)
            self.query_panel.clear_session_context()

        error_msg = str(error)
        self._show_critical(
            "Query Error",
            f"An error occurred while running your query:\n\n{error_msg}"
        )

        self._set_status_message("Query failed")
        self._refresh_status_metrics()
        payload = self._build_query_payload(
            session_id or self._active_session_id,
            status="failed",
            extra={
                "error_type": error.__class__.__name__,
                "error_message": error_msg,
            },
        )
        telemetry.emit("ui.query.failed", payload)
        self._finalise_session_state()

    def on_query_cancelled(self, session_id: str) -> None:
        """Handle cancellation requests from the query panel."""

        if not self.is_query_running:
            return

        if self._active_session_id and session_id != self._active_session_id:
            return

        reply = self._ask_question(
            "Cancel running query",
            (
                "The current query is still running. Do you want to stop it? "
                "Any partial progress will be lost."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            if self.query_panel:
                self.query_panel.set_busy(True)
            return

        self._set_status_message("Cancelling…")

        self._cancelled_session_ids.add(session_id)
        self.is_query_running = False
        self.progress_bar.setVisible(False)

        if self.query_panel:
            self.query_panel.set_busy(False)
            self.query_panel.clear_session_context()

        self._set_status_message("Query cancelled")
        payload = self._build_query_payload(session_id, status="cancelled")
        telemetry.emit("ui.query.cancelled", payload)
        self._finalise_session_state()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Clean up any running queries
        if self.is_query_running:
            reply = self._ask_question(
                "Confirm Close",
                "A query is currently running. Do you want to close anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

        if self.metrics_timer:
            self.metrics_timer.stop()
        event.accept()

    def _resolve_session_id(self) -> str:
        """Return the session identifier for the next query run."""

        if self.query_panel:
            existing = self.query_panel.get_active_session_id()
            if existing:
                return existing

        session_id = uuid.uuid4().hex
        if self.query_panel:
            self.query_panel.set_session_identifier(session_id)
        return session_id

    def _compute_duration_ms(self) -> Optional[float]:
        """Compute the elapsed runtime for the active query."""

        if self._query_started_at is None:
            return None

        elapsed_ms = (monotonic() - self._query_started_at) * 1000
        return max(0.0, elapsed_ms)

    def _build_query_payload(
        self,
        session_id: Optional[str],
        *,
        status: str,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Compose a telemetry payload for query lifecycle events."""

        payload: dict[str, Any] = {
            "session_id": session_id,
            "status": status,
            "query_length": len(self.current_query.strip()),
        }

        if self.query_panel:
            payload["reasoning_mode"] = self.query_panel.current_reasoning_mode
            payload["loops"] = self.query_panel.current_loops

        duration_ms = self._compute_duration_ms()
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms

        if extra:
            payload.update(extra)

        return {key: value for key, value in payload.items() if value is not None}

    def _finalise_session_state(self) -> None:
        """Reset session bookkeeping after a terminal query state."""

        self._active_session_id = None
        self._query_started_at = None
        self._active_worker = None

    def _start_metrics_timer(self) -> None:
        """Start the timer responsible for refreshing status metrics."""

        if self.metrics_timer:
            return

        self.metrics_timer = QTimer(self)
        self.metrics_timer.setInterval(2000)
        self.metrics_timer.timeout.connect(self._refresh_status_metrics)
        self.metrics_timer.start()

    def _set_status_message(self, message: str) -> None:
        """Update the persistent status bar message."""

        self._status_message = message
        self.statusBar().showMessage(message)

    def _invoke_query_text_method(self, method_name: str) -> None:
        """Invoke a QTextEdit editing command on the query panel when available."""

        if not self.query_panel or not getattr(self.query_panel, "query_input", None):
            return

        query_input = self.query_panel.query_input
        if query_input and hasattr(query_input, method_name):
            getattr(query_input, method_name)()

    def _trigger_export_action(self) -> None:
        """Surface the exports dock and guide the user to available exports."""

        if self.export_dock:
            self.export_dock.show()
            self.export_dock.raise_()

        if self.export_manager and self.export_manager.isVisible():
            self._set_status_message("Select an export target from the Exports panel.")
            return

        self._show_information(
            "Exports",
            "Use the Exports panel to run the desired export for the active session.",
        )

    def _open_help_center(self) -> None:
        """Display guidance on where to find desktop documentation."""

        self._show_information(
            "Autoresearch Help",
            (
                "Refer to the desktop README for workflow guidance and visit the online "
                "documentation for advanced topics."
            ),
        )

    def _show_about_dialog(self) -> None:
        """Show an about dialog with release metadata."""

        release = os.environ.get("AUTORESEARCH_RELEASE", "development")
        self._show_information(
            "About Autoresearch",
            (
                "Autoresearch Desktop\n\n"
                "AI-assisted research orchestration with dialectical reasoning.\n"
                f"Release channel: {release}"
            ),
        )

    def _refresh_status_metrics(self) -> None:
        """Refresh CPU, memory, and token metrics in the status bar."""

        cpu_text = "CPU: --%"
        memory_text = "Memory: -- MB"
        tokens_text = "Tokens: --"

        metrics_obj = self._metrics_provider() if self._metrics_provider else None
        latest_usage: tuple[float, float, float, float, float] | None = None
        tokens_total: Optional[int] = None

        if metrics_obj is not None:
            usage_history = getattr(metrics_obj, "resource_usage", None)
            if usage_history:
                latest_usage = usage_history[-1]
            token_counts = getattr(metrics_obj, "token_counts", None)
            if token_counts:
                total_in = sum(int(counts.get("in", 0)) for counts in token_counts.values())
                total_out = sum(int(counts.get("out", 0)) for counts in token_counts.values())
                tokens_total = total_in + total_out

        if latest_usage:
            _, cpu_percent, memory_mb, _, _ = latest_usage
            if isinstance(cpu_percent, (int, float)):
                cpu_text = f"CPU: {cpu_percent:.0f}%"
            if isinstance(memory_mb, (int, float)):
                memory_text = f"Memory: {memory_mb:.0f} MB"

        if tokens_total is None:
            tokens_total = self._extract_token_total(self._latest_metrics_payload)

        if tokens_total is not None:
            tokens_text = f"Tokens: {tokens_total:,}"

        if self._metric_labels.get("cpu"):
            self._metric_labels["cpu"].setText(cpu_text)
        if self._metric_labels.get("memory"):
            self._metric_labels["memory"].setText(memory_text)
        if self._metric_labels.get("tokens"):
            self._metric_labels["tokens"].setText(tokens_text)

    def _extract_token_total(self, metrics: Mapping[str, Any] | None) -> Optional[int]:
        """Extract a total token count from a metrics payload when available."""

        if not isinstance(metrics, Mapping):
            return None

        tokens_payload = metrics.get("tokens")
        if isinstance(tokens_payload, Mapping):
            for key in ("total", "count", "used", "tokens"):
                value = tokens_payload.get(key)
                if isinstance(value, (int, float)):
                    return int(value)
            input_tokens = tokens_payload.get("input")
            output_tokens = tokens_payload.get("output")
            if isinstance(input_tokens, (int, float)) or isinstance(output_tokens, (int, float)):
                total_value = int(input_tokens or 0) + int(output_tokens or 0)
                if total_value:
                    return total_value
        elif isinstance(tokens_payload, (int, float)):
            return int(tokens_payload)

        total_tokens_payload = metrics.get("total_tokens")
        if isinstance(total_tokens_payload, Mapping):
            total_value = total_tokens_payload.get("total")
            if isinstance(total_value, (int, float)):
                return int(total_value)
            input_tokens = total_tokens_payload.get("input")
            output_tokens = total_tokens_payload.get("output")
            if isinstance(input_tokens, (int, float)) or isinstance(output_tokens, (int, float)):
                return int(input_tokens or 0) + int(output_tokens or 0)

        return None
