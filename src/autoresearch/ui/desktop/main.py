"""
Main entry point for the PySide6 desktop application.

This module provides the main function to launch the Autoresearch
desktop interface and handles application initialization.
"""

from __future__ import annotations

import sys
from typing import Optional

# Import before creating QApplication to avoid Qt-related issues
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox
except ImportError as e:
    print(f"Error: PySide6 is not installed. Please install it with: uv add PySide6")
    print(f"Import error: {e}")
    sys.exit(1)

# Import desktop components after PySide6 is confirmed available
from .main_window import AutoresearchMainWindow


def main() -> int:
    """
    Launch the Autoresearch desktop application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Configure high DPI scaling before creating the QApplication instance.
    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_EnableHighDpiScaling,
        True,
    )
    if hasattr(QApplication, "setHighDpiScaleFactorRoundingPolicy") and hasattr(
        Qt, "HighDpiScaleFactorRoundingPolicy"
    ):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setApplicationName("Autoresearch")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Autoresearch Project")

    # Set application icon (if available)
    # app.setWindowIcon(QIcon("path/to/icon.png"))

    try:
        # Create and show main window
        window = AutoresearchMainWindow()
        window.show()

        # Start event loop
        return app.exec()

    except Exception as e:
        # Show error dialog if something goes wrong
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Autoresearch - Startup Error")
        error_box.setText("Failed to start Autoresearch desktop application.")
        error_box.setDetailedText(str(e))
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.exec()

        print(f"Startup error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
