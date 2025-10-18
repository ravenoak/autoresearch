"""
Query input panel for the PySide6 desktop interface.

Provides a clean, intuitive interface for entering research queries
and configuring reasoning parameters.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSlider, QSpinBox, QTextEdit, QVBoxLayout, QWidget
)

try:
    from ...orchestration import ReasoningMode
except ImportError:
    # For standalone development
    ReasoningMode = None


class QueryPanel(QWidget):
    """
    Panel for entering queries and configuring reasoning parameters.

    Provides an intuitive interface for:
    - Query text input
    - Reasoning mode selection
    - Loop count configuration
    - Query submission
    """

    # Signals
    query_submitted = Signal(str)  # Emitted when user submits a query

    def __init__(self) -> None:
        """Initialize the query panel."""
        super().__init__()

        # UI components
        self.query_input: Optional[QTextEdit] = None
        self.reasoning_mode_combo: Optional[QComboBox] = None
        self.loops_spinbox: Optional[QSpinBox] = None
        self.run_button: Optional[QPushButton] = None

        # Current values
        self.current_reasoning_mode: str = "balanced"
        self.current_loops: int = 3

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Query input group
        query_group = QGroupBox("Research Query")
        query_layout = QVBoxLayout(query_group)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your research query here...")
        self.query_input.setMinimumHeight(100)
        self.query_input.setMaximumHeight(200)
        query_layout.addWidget(self.query_input)

        layout.addWidget(query_group)

        # Configuration group
        config_group = QGroupBox("Reasoning Configuration")
        config_layout = QFormLayout(config_group)

        # Reasoning mode selection
        self.reasoning_mode_combo = QComboBox()
        if ReasoningMode:
            self.reasoning_mode_combo.addItems([mode.value for mode in ReasoningMode])
        else:
            # Fallback for standalone development
            self.reasoning_mode_combo.addItems(["direct", "balanced", "comprehensive"])
        self.reasoning_mode_combo.setCurrentText("balanced")
        config_layout.addRow("Reasoning Mode:", self.reasoning_mode_combo)

        # Loops configuration
        self.loops_spinbox = QSpinBox()
        self.loops_spinbox.setRange(1, 10)
        self.loops_spinbox.setValue(3)
        self.loops_spinbox.setSuffix(" loops")
        config_layout.addRow("Reasoning Loops:", self.loops_spinbox)

        layout.addWidget(config_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Query")
        self.run_button.setMinimumHeight(40)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.run_button)

        # Add some spacing
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Add stretch to push everything to the top
        layout.addStretch()

    def setup_connections(self) -> None:
        """Set up signal-slot connections."""
        if self.run_button:
            self.run_button.clicked.connect(self.on_run_clicked)

        if self.reasoning_mode_combo:
            self.reasoning_mode_combo.currentTextChanged.connect(self.on_reasoning_mode_changed)

        if self.loops_spinbox:
            self.loops_spinbox.valueChanged.connect(self.on_loops_changed)

    def on_run_clicked(self) -> None:
        """Handle run button click."""
        if not self.query_input:
            return

        query = self.query_input.toPlainText().strip()
        if query:
            self.query_submitted.emit(query)

    def on_reasoning_mode_changed(self, mode: str) -> None:
        """Handle reasoning mode selection change."""
        self.current_reasoning_mode = mode

    def on_loops_changed(self, loops: int) -> None:
        """Handle loops value change."""
        self.current_loops = loops

    def get_configuration(self) -> dict:
        """Get current configuration settings."""
        return {
            "reasoning_mode": self.current_reasoning_mode,
            "loops": self.current_loops
        }

    def set_query_text(self, text: str) -> None:
        """Set the query text (useful for loading saved queries)."""
        if self.query_input:
            self.query_input.setPlainText(text)

    def clear_query(self) -> None:
        """Clear the query input."""
        if self.query_input:
            self.query_input.clear()

    def focus_query_input(self) -> None:
        """Set focus to the query input field."""
        if self.query_input:
            self.query_input.setFocus()
