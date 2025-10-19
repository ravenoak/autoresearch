# PySide6 Desktop Interface Developer Guide

## Overview

The PySide6 desktop interface provides a professional, native GUI for Autoresearch using Qt for Python. This guide covers development, testing, and deployment of the desktop interface.

## Architecture

### Component Structure

```
src/autoresearch/ui/desktop/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── main_window.py           # Main window implementation
├── query_panel.py           # Query input and controls
├── results_display.py       # Results visualization
├── knowledge_graph_view.py  # Dedicated graph viewer widget
├── metrics_dashboard.py     # Hierarchical metrics inspector
├── config_editor.py         # JSON-based configuration editor
├── session_manager.py       # Recent session listing and navigation
└── export_manager.py        # Export action launcher
```

### Key Components

#### MainWindow (QMainWindow)
- Central application window with splitter layout
- Menu bar (File, Edit, View, Help)
- Status bar with real-time metrics
- Dock widgets for secondary information

#### QueryPanel (QWidget)
- Query text input (QTextEdit)
- Reasoning mode selection (QComboBox)
- Loop count configuration (QSpinBox)
- Query submission controls

#### ResultsDisplay (QTabWidget)
- Multiple tabs for different result views
- Markdown rendering (QWebEngineView)
- Knowledge graph visualization via `KnowledgeGraphView`
- Agent trace display
- Performance metrics via `MetricsDashboard`

#### Dock Widgets
- **ConfigEditor**: Emits `configuration_changed` with JSON-ready dicts that the main
  window validates against `ConfigModel` when available.
- **SessionManager**: Lists prior queries; activating an item emits
  `session_selected` so future iterations can load persisted state.
- **ExportManager**: Renders export buttons (GraphML, JSON, etc.) based on the
  latest `result.metrics['knowledge_graph']['exports']` payload.

## Development Setup

### Prerequisites

```bash
# Install PySide6 and desktop dependencies
uv add PySide6 markdown networkx matplotlib

# For development
uv sync --extra desktop

# For testing (optional)
uv add pytest-qt pytest-mock
```

### Running the Application

```bash
# Run the desktop application
uv run python -m autoresearch.ui.desktop.main

# Or directly
uv run python src/autoresearch/ui/desktop/main.py
```

### Development Workflow

1. **Edit code** in the desktop package
2. **Test changes** by running the application
3. **Run tests** with `uv run pytest tests/ui/desktop/`
4. **Check linting** with `uv run task check`

## UI Guidelines

### Qt Design Principles

1. **Native Look and Feel**: Use platform-specific styling where appropriate
2. **Keyboard Navigation**: Ensure all functionality is keyboard accessible
3. **Responsive Layout**: Handle different window sizes gracefully
4. **High DPI Support**: Use scalable units and proper DPI handling

### Layout Guidelines

#### Use QVBoxLayout and QHBoxLayout for main structure
```python
layout = QVBoxLayout()
# Add widgets vertically
layout.addWidget(query_panel)
layout.addWidget(results_display)
```

#### Use QSplitter for resizable sections
```python
splitter = QSplitter(Qt.Vertical)
splitter.addWidget(panel1)
splitter.addWidget(panel2)
splitter.setSizes([200, 400])  # Initial proportions
```

#### Use QFormLayout for configuration forms
```python
form_layout = QFormLayout()
form_layout.addRow("Reasoning Mode:", combo_box)
form_layout.addRow("Loops:", spin_box)
```

### Styling Guidelines

#### Use Qt Style Sheets for custom styling
```python
button.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
""")
```

#### Follow platform conventions for colors and fonts
- Use system palette for consistency
- Respect dark/light mode preferences
- Use appropriate font sizes for readability

## Testing

### Test Structure

```
tests/ui/desktop/
├── __init__.py
├── test_component_smoke.py  # pytest-qt smoke tests for desktop widgets
└── integration/
    └── test_desktop_integration.py  # Full workflow tests
```

### Testing Patterns

#### Widget Testing
```python
import pytest
from PySide6.QtWidgets import QApplication
from autoresearch.ui.desktop.query_panel import QueryPanel

from PySide6.QtWidgets import QTreeWidgetItem


def test_metrics_dashboard_updates(qtbot):
    dashboard = MetricsDashboard()
    qtbot.addWidget(dashboard)
    dashboard.update_metrics({"tokens": {"prompt": 42, "completion": 64}})
    assert dashboard.findChildren(QTreeWidgetItem)

def test_query_panel_creation(app):
    panel = QueryPanel()
    assert panel.query_input is not None
    assert panel.run_button is not None
```

#### Signal Testing
```python
def test_query_submission(app, qtbot):
    panel = QueryPanel()
    query_submitted = []

    def on_query_submitted(query):
        query_submitted.append(query)

    panel.query_submitted.connect(on_query_submitted)

    # Simulate user input
    panel.query_input.setPlainText("test query")
    qtbot.mouseClick(panel.run_button, Qt.LeftButton)

    assert len(query_submitted) == 1
    assert query_submitted[0] == "test query"
```

#### Integration Testing
```python
def test_full_query_workflow(app, qtbot):
    window = AutoresearchMainWindow()

    # Set up mock orchestrator
    window.orchestrator = MockOrchestrator()

    # Enter query
    window.query_panel.query_input.setPlainText("test query")
    qtbot.mouseClick(window.query_panel.run_button, Qt.LeftButton)

    # Wait for results
    qtbot.wait(1000)  # Adjust based on mock response time

    # Verify results displayed
    assert window.results_display.current_result is not None
```

### Running Tests

```bash
# Run all desktop UI tests
uv run pytest tests/ui/desktop/

# Run specific test file
uv run pytest tests/ui/desktop/test_query_panel.py

# Run with coverage
uv run pytest tests/ui/desktop/ --cov=src/autoresearch/ui/desktop
```

## Common Patterns

### Async Operations

Use QThreadPool for background operations to keep UI responsive:

```python
from PySide6.QtCore import QThreadPool, QRunnable

class QueryWorker(QRunnable):
    def __init__(self, orchestrator, query, config):
        super().__init__()
        self.orchestrator = orchestrator
        self.query = query
        self.config = config

    def run(self):
        try:
            result = self.orchestrator.run_query(self.query, self.config)
            # Emit signal to update UI (implement signal mechanism)
        except Exception as e:
            # Handle error (implement error signal)

# In main window
worker = QueryWorker(self.orchestrator, query, self.config)
QThreadPool.globalInstance().start(worker)
```

### Progress Updates

Use QProgressDialog for long-running operations:

```python
from PySide6.QtWidgets import QProgressDialog

progress = QProgressDialog("Running query...", "Cancel", 0, 0, self)
progress.setWindowModality(Qt.WindowModal)
progress.show()

# Update progress (implement progress signal)
progress.setLabelText("Processing results...")
```

### Settings Persistence

Use QSettings for application preferences:

```python
from PySide6.QtCore import QSettings

settings = QSettings("Autoresearch", "Desktop")

# Save setting
settings.setValue("window/geometry", self.saveGeometry())
settings.setValue("ui/theme", "dark")

# Load setting
geometry = settings.value("window/geometry")
if geometry:
    self.restoreGeometry(geometry)
```

## Performance Optimization

### Memory Management

1. **Clean up resources**: Properly delete widgets and disconnect signals
2. **Lazy loading**: Load heavy components only when needed
3. **Image caching**: Cache rendered images to avoid recomputation

### Rendering Performance

1. **Use QGraphicsView** for complex visualizations
2. **Implement virtual scrolling** for large datasets
3. **Batch updates** to avoid excessive repaints

### Startup Performance

1. **Lazy imports**: Import heavy modules only when needed
2. **Progressive loading**: Show basic UI first, load features on demand
3. **Caching**: Cache expensive computations

## Cross-Platform Development

### Platform-Specific Considerations

#### Windows
- Use Windows-specific styling
- Handle DPI scaling properly
- Test with different Windows versions

#### macOS
- Follow macOS HIG (Human Interface Guidelines)
- Use native macOS widgets where possible
- Handle macOS-specific keyboard shortcuts

#### Linux
- Test with different desktop environments (GNOME, KDE, etc.)
- Handle different theme engines
- Ensure proper font rendering

### Packaging

#### Windows
```bash
# Create Windows executable
pyinstaller --windowed src/autoresearch/ui/desktop/main.py
```

#### macOS
```bash
# Create macOS app bundle
pyinstaller --windowed --osx-bundle-identifier com.autoresearch.desktop src/autoresearch/ui/desktop/main.py
```

#### Linux
```bash
# Create Linux AppImage or Flatpak
# (Requires additional packaging tools)
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Install missing dependencies
uv add PySide6

# On Linux, install system dependencies
sudo apt-get install qt6-base-dev  # Ubuntu/Debian
# or
sudo pacman -S qt6-base          # Arch Linux
```

#### High DPI Issues
```python
# Enable high DPI scaling in main.py
if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    # ...
```

#### WebEngine Issues
```bash
# Install WebEngine dependencies (Linux)
sudo apt-get install qt6-webengine-dev
```

### Debug Mode

Run with debug output:
```bash
QT_LOGGING_RULES="*.debug=true" uv run python src/autoresearch/ui/desktop/main.py
```

## Contributing

### Code Style

1. **Follow Qt conventions** for widget naming and layout
2. **Use descriptive names** for UI elements
3. **Document complex UI logic** with comments
4. **Keep components focused** on single responsibilities

### Review Checklist

- [ ] UI responds correctly to all user inputs
- [ ] Keyboard navigation works for all interactive elements
- [ ] Application works on target platforms
- [ ] Performance is acceptable for typical use cases
- [ ] Error handling provides helpful feedback
- [ ] Accessibility features are properly implemented
- [ ] Tests cover new functionality

### Performance Guidelines

- **Target < 2 second startup time** on modern hardware
- **Keep memory usage < 200MB** for typical sessions
- **Ensure UI remains responsive** during query execution
- **Optimize rendering** for large result sets

## Migration from Streamlit

### Key Differences

| Aspect | Streamlit | PySide6 |
|--------|-----------|---------|
| Architecture | Web-based, reactive | Desktop, event-driven |
| Performance | Browser overhead | Native, GPU accelerated |
| Deployment | Web server required | Standalone executable |
| Customization | Limited by web constraints | Full native control |
| User Experience | Web-like | Native desktop feel |

### Migration Strategy

1. **Component-by-component**: Replace Streamlit components with Qt equivalents
2. **Maintain API compatibility**: Keep core logic unchanged during migration
3. **Progressive enhancement**: Add desktop-specific features gradually
4. **Parallel development**: Keep both interfaces working during transition

### Benefits of Migration

1. **Better Performance**: Native rendering, no browser overhead
2. **Professional Feel**: Matches expectations for research tools
3. **Rich Interactions**: Multi-window, drag-and-drop, annotations
4. **Offline Operation**: No server dependency
5. **Long-term Maintenance**: Qt is more stable than web frameworks

This developer guide provides the foundation for building and maintaining the PySide6 desktop interface. As the interface evolves, update this guide to reflect new patterns and best practices.