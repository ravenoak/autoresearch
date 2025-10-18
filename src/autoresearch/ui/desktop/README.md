# Autoresearch Desktop Interface

## Overview

The PySide6 desktop interface provides a professional, native GUI for Autoresearch using Qt for Python. This interface offers a superior user experience compared to web-based alternatives with:

- **Native Performance**: GPU-accelerated rendering, no browser overhead
- **Rich Interactions**: Multi-window support, drag-and-drop, keyboard shortcuts
- **Professional Feel**: Matches expectations for serious research tools
- **Offline Operation**: No server required, works completely offline

## Installation

### Prerequisites

```bash
# Install PySide6 and desktop dependencies
uv add PySide6 markdown networkx matplotlib

# For development
uv sync --extra desktop
```

### Running the Application

```bash
# Launch the desktop application
uv run python -m autoresearch.ui.desktop.main

# Or via CLI command
autoresearch desktop
```

## Features

### Query Interface
- **Query Input**: Multi-line text area for research queries
- **Reasoning Configuration**: Select reasoning mode and loop count
- **Real-time Progress**: Visual feedback during query execution
- **Error Handling**: Clear error messages with actionable suggestions

### Results Display
- **Tabbed Interface**: Organized views for different result aspects
- **Markdown Rendering**: Rich formatting for answers and explanations
- **Knowledge Graph Visualization**: Interactive graph display (planned)
- **Agent Trace**: Step-by-step reasoning breakdown
- **Performance Metrics**: Real-time monitoring of query execution

### Professional Features
- **Multi-Window Support**: Compare multiple queries side-by-side
- **Keyboard Shortcuts**: Efficient navigation for power users
- **Session Management**: Persistent workspaces and query history
- **Export Options**: Save results in multiple formats (Markdown, JSON, PDF)

## Architecture

### Component Structure

```
main.py              # Application entry point
main_window.py       # Main window with menu and layout
query_panel.py       # Query input and configuration
results_display.py   # Tabbed results visualization
```

### Key Components

#### MainWindow (QMainWindow)
- Central application window with splitter layout
- Menu bar with File, Edit, View, Help menus
- Status bar with real-time metrics
- Dock widgets for secondary information

#### QueryPanel (QWidget)
- Query text input with syntax highlighting
- Reasoning mode selection (QComboBox)
- Loop count configuration (QSpinBox)
- Query submission with progress indication

#### ResultsDisplay (QTabWidget)
- Multiple tabs for different result views
- Markdown rendering with QWebEngineView
- Knowledge graph visualization area
- Performance metrics dashboard

## Development

### Code Style

Follow Qt conventions for widget naming and layout:
- Use descriptive names for UI elements
- Follow platform-specific design guidelines
- Maintain consistent spacing and alignment
- Use proper signal-slot connections

### Testing

```bash
# Run desktop UI tests
uv run pytest tests/ui/desktop/

# Run with coverage
uv run pytest tests/ui/desktop/ --cov=src/autoresearch/ui/desktop
```

### Performance Guidelines

- **Startup Time**: Target < 2 seconds on modern hardware
- **Memory Usage**: Keep under 200MB for typical sessions
- **UI Responsiveness**: Maintain smooth interaction during queries
- **Resource Management**: Proper cleanup of threads and resources

## Migration from Streamlit

The desktop interface replaces the previous Streamlit web interface with:

| Aspect | Streamlit | PySide6 Desktop |
|--------|-----------|-----------------|
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

## Platform Support

### Windows
- Native Windows styling and behavior
- Support for Windows 10+ (64-bit)
- Proper DPI scaling support

### macOS
- Native macOS appearance and HIG compliance
- Support for macOS 11+ (Intel and Apple Silicon)
- Proper window management integration

### Linux
- Cross-desktop environment support (GNOME, KDE, etc.)
- Wayland and X11 compatibility
- Proper theme engine integration

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Install missing dependencies
uv add PySide6

# On Linux, install system dependencies
sudo apt-get install qt6-base-dev  # Ubuntu/Debian
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
```

#### WebEngine Issues (Linux)
```bash
# Install WebEngine dependencies
sudo apt-get install qt6-webengine-dev
```

## Contributing

### Development Workflow

1. **Edit code** in the desktop package
2. **Test changes** by running the application
3. **Run tests** with `uv run pytest tests/ui/desktop/`
4. **Check linting** with `uv run task check`

### Code Review Checklist

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

## Future Enhancements

### Planned Features
- [ ] Interactive knowledge graph with zoom and pan
- [ ] Advanced search and filtering of query history
- [ ] Custom annotation and bookmarking system
- [ ] Integration with external tools (Obsidian, Zotero)
- [ ] Plugin system for custom visualizations

### Roadmap
- **v0.1.0**: Basic functionality (query input, results display)
- **v0.2.0**: Advanced features (multi-window, annotations, exports)
- **v1.0.0**: Full feature parity with web interface + desktop enhancements

---

This desktop interface represents a significant upgrade in user experience for Autoresearch, providing the professional, high-performance research environment that matches the tool's local-first philosophy and target user needs.
