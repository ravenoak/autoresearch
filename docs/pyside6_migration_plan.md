# PySide6 Migration and Streamlit Removal Plan

## Overview

This document outlines the comprehensive plan for migrating Autoresearch from Streamlit to PySide6 as the primary desktop GUI interface, and removing Streamlit dependencies. The migration focuses on providing a professional, native desktop experience while maintaining all existing functionality.

## Migration Rationale

### Why PySide6?

1. **Professional Interface**: Qt provides native desktop applications used by Autodesk, Mercedes, and other professional tools
2. **Performance**: Native GPU-accelerated rendering vs browser overhead
3. **Rich Interactions**: Multi-window support, drag-and-drop, keyboard shortcuts, annotations
4. **Local-First Alignment**: Desktop app matches the local-first architecture philosophy
5. **Long-Term Stability**: Qt has 30+ years of development vs web frameworks that change rapidly

### Why Not Keep Streamlit?

1. **Architectural Issues**: Monolithic 2,500-line file, testing difficulties, maintenance burden
2. **Performance Limitations**: Browser-based, slow initial loads, memory intensive
3. **Limited Customization**: Streamlit's opinionated design restricts advanced features
4. **Maintenance Burden**: Background threads causing test hangs, complex state management

## Migration Timeline

### Phase 1: PySide6 POC Implementation (2 weeks)
- [ ] Set up PySide6 development environment
- [ ] Create minimal viable desktop application
- [ ] Implement basic query input and results display
- [ ] Validate core functionality works
- [ ] Gather initial feedback on native experience

### Phase 2: Feature Parity Implementation (6 weeks)
- [ ] Implement all Streamlit features in PySide6:
  - [ ] Configuration editor with presets
  - [ ] Knowledge graph visualization
  - [ ] Agent trace display
  - [ ] Real-time metrics dashboard
  - [ ] Progressive disclosure controls
  - [ ] Export functionality (Markdown, JSON, GraphML)
  - [ ] Accessibility features (WCAG 2.1 AA compliance)

### Phase 3: Professional Features (4 weeks)
- [ ] Multi-window support for comparing queries
- [ ] Advanced knowledge graph interactions (zoom, pan, annotations)
- [ ] Keyboard shortcuts and navigation
- [ ] Drag-and-drop document loading
- [ ] Session persistence and workspace management
- [ ] Professional theming (light/dark mode)
- [ ] Export pipeline (PDF reports, annotated graphs)

### Phase 4: Testing and Quality Assurance (3 weeks)
- [ ] Comprehensive test suite for PySide6 interface
- [ ] Cross-platform testing (Windows, macOS, Linux)
- [ ] Performance benchmarking vs Streamlit
- [ ] Accessibility testing and validation
- [ ] User acceptance testing with target users

### Phase 5: Deprecation and Removal (2 weeks)
- [ ] Mark Streamlit as deprecated in documentation
- [ ] Provide migration guide for existing users
- [ ] Remove Streamlit code after 1-2 release cycles
- [ ] Update CI/CD to test PySide6 instead of Streamlit
- [ ] Archive Streamlit-related test files

## Technical Architecture

### PySide6 Application Structure

```
src/autoresearch/ui/desktop/
├── __init__.py
├── main_window.py          # Main application window
├── query_panel.py          # Query input and controls
├── results_display.py      # Results tabs and content
├── knowledge_graph_view.py # Interactive graph visualization
├── metrics_dashboard.py    # Real-time metrics display
├── config_editor.py        # Configuration management
├── session_manager.py      # Window/workspace management
└── export_manager.py       # Export functionality
```

### Key Components

#### 1. MainWindow (QMainWindow)
- Central widget with splitter layout
- Menu bar with File, Edit, View, Help
- Status bar with real-time metrics
- Dock widgets for secondary information
- Full keyboard shortcut support

#### 2. QueryPanel (QWidget)
- Text area for query input
- Reasoning mode selector (QComboBox)
- Loops slider (QSlider)
- Run query button (QPushButton)
- Progress indicator during execution

#### 3. ResultsDisplay (QTabWidget)
- Answer tab with Markdown rendering (QWebEngineView)
- Knowledge Graph tab with interactive visualization
- Agent Trace tab with step-by-step breakdown
- Metrics tab with live-updating charts
- Citations tab with source management

#### 4. KnowledgeGraphView (QGraphicsView)
- Interactive graph rendering with NetworkX
- Zoom and pan controls
- Node/edge selection and inspection
- Export to various formats (PNG, PDF, SVG)

#### 5. MetricsDashboard (QWidget)
- Real-time CPU/memory usage charts
- Agent performance metrics
- Token usage tracking
- System health indicators

## Dependencies and Installation

### New Dependencies
```toml
# pyproject.toml additions
[project.dependencies]
"PySide6 >=6.6.0"
"markdown >=3.5.0"           # For Markdown rendering
"networkx >=3.2.0"           # For graph visualization
"matplotlib >=3.8.0"         # For charts and graphs
"plotly >=5.17.0"            # For interactive visualizations

[project.optional-dependencies]
desktop = [
    "PySide6 >=6.6.0",
    "markdown >=3.5.0",
    "networkx >=3.2.0",
    "matplotlib >=3.8.0",
    "plotly >=5.17.0",
]
```

### Installation Commands
```bash
# Install PySide6 and desktop dependencies
uv add PySide6 markdown networkx matplotlib plotly

# Install in development mode
uv pip install -e . --extra desktop

# Run the PySide6 application
uv run python -m autoresearch.ui.desktop.main
```

## Migration Strategy

### 1. Gradual Feature Migration
- Start with core query functionality
- Add visualization features progressively
- Maintain CLI/API as primary interfaces during migration
- Keep Streamlit as fallback during development

### 2. Parallel Development
- Develop PySide6 interface alongside existing Streamlit
- Share core logic (orchestrator, output formatting, etc.)
- Test both interfaces against same backend
- Allow users to choose interface preference

### 3. User Communication
- Announce PySide6 as "experimental" initially
- Document migration benefits and timeline
- Provide both interfaces during transition period
- Gather user feedback on PySide6 experience

### Legacy Streamlit Opt-In
- Gate the legacy `autoresearch gui` command behind the
  `AUTORESEARCH_ENABLE_STREAMLIT` environment variable during the grace period.
- When the flag is not set, emit a migration warning and direct teams to
  `autoresearch desktop` so the PySide6 workflow becomes the default habit.
- Publish the opt-in command in release notes and internal announcements:

  ```bash
  AUTORESEARCH_ENABLE_STREAMLIT=1 autoresearch gui --no-browser
  ```

- Remove the opt-in instructions once Streamlit support is fully sunset.

## Testing Strategy

### New Test Structure

The PySide6 desktop test suite lives under `tests/ui/desktop/`. Delivered
modules are marked with a checked box so current coverage is visible, while the
remaining backlog is tracked separately with clear owners and phase targets.

#### Delivered Modules
- <a id="delivered-test-component-smoke"></a>[x]
  `tests/ui/desktop/test_component_smoke.py` - Validates the PySide6 bootstrap
  and baseline UI wiring; maps to
  [Query submission and results display](#scenario-query-results).
- <a id="delivered-test-query-panel"></a>[x]
  `tests/ui/desktop/test_query_panel.py` - Exercises interactive controls for
  the query form; maps to
  [Query submission and results display](#scenario-query-results) and
  [Keyboard navigation and shortcuts](#scenario-keyboard).
- <a id="delivered-test-results-display"></a>[x]
  `tests/ui/desktop/test_results_display.py` - Covers rendering of responses and
  citations; maps to
  [Query submission and results display](#scenario-query-results).
- <a id="delivered-test-desktop-integration"></a>[x]
  `tests/ui/desktop/test_desktop_integration.py` - Provides end-to-end smoke
  coverage for window bootstrap; maps to
  [Multi-window session management](#scenario-multi-window).

#### Backlog Checklist (Unimplemented)
- <a id="backlog-test-main-window"></a>[ ]
  `tests/ui/desktop/test_main_window.py` - Owner: Desktop Guild; Target: Phase 1
  (POC) once the main window API stabilizes.
- <a id="backlog-test-knowledge"></a>[ ]
  `tests/ui/desktop/test_knowledge_graph.py` - Owner: Graph Visualization Pod;
  Target: Phase 2 (Feature Parity) alongside the knowledge graph widget.
- <a id="backlog-test-metrics"></a>[ ]
  `tests/ui/desktop/test_metrics_dashboard.py` - Owner: Metrics Squad; Target:
  Phase 2 (Feature Parity) when telemetry panels ship.
- <a id="backlog-test-gui-integration"></a>[ ]
  `tests/ui/desktop/integration/test_gui_integration.py` - Owner: Desktop Guild;
  Target: Phase 3 (Professional Features) after workspace flows land.
- <a id="backlog-test-cross-platform"></a>[ ]
  `tests/ui/desktop/integration/test_cross_platform.py` - Owner: QA Team;
  Target: Phase 4 (Testing and QA) for platform matrix validation.

### Test Categories
1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: Component interaction and workflows
3. **BDD Tests**: User behavior scenarios
4. **Accessibility Tests**: WCAG compliance validation
5. **Performance Tests**: Rendering speed, memory usage
6. **Cross-Platform Tests**: Windows, macOS, Linux compatibility

### Key Test Scenarios
- <a id="scenario-query-results"></a>[x] Query submission and results display
  - Covered by
    [`test_component_smoke.py`](#delivered-test-component-smoke),
    [`test_query_panel.py`](#delivered-test-query-panel), and
    [`test_results_display.py`](#delivered-test-results-display).
- <a id="scenario-configuration"></a>[ ] Configuration editor functionality
  - Pending; planned in
    [`test_main_window.py`](#backlog-test-main-window) once configuration panes
    are in place.
- <a id="scenario-knowledge"></a>[ ] Knowledge graph interaction (zoom, pan,
  select)
  - Pending; covered when
    [`test_knowledge_graph.py`](#backlog-test-knowledge) lands.
- <a id="scenario-multi-window"></a>[x] Multi-window session management
  - Partially covered by
    [`test_desktop_integration.py`](#delivered-test-desktop-integration); full
    coverage requires
    [`test_gui_integration.py`](#backlog-test-gui-integration).
- <a id="scenario-export"></a>[ ] Export functionality (all formats)
  - Pending; to be addressed in the integration backlog once export flows are
    implemented.
- <a id="scenario-keyboard"></a>[x] Keyboard navigation and shortcuts
  - Exercised through
    [`test_query_panel.py`](#delivered-test-query-panel); additional coverage is
    expected in `test_main_window.py`.
- <a id="scenario-accessibility"></a>[ ] Screen reader compatibility
  - Pending accessibility audit; tests will be captured in a11y-specific
    modules during Phase 4.
- <a id="scenario-performance"></a>[ ] Performance under load
  - Pending; to be validated via dedicated benchmarks and the platform
    integration backlog.

## Risk Mitigation

### Technical Risks
1. **PySide6 Learning Curve**: Mitigate with comprehensive documentation and POC-first approach
2. **Cross-Platform Issues**: Test on all target platforms early and often
3. **Performance Regression**: Benchmark against Streamlit and optimize hot paths
4. **Dependency Conflicts**: Use dependency resolver and test integration thoroughly

### User Experience Risks
1. **Feature Parity**: Document any missing features and roadmap
2. **User Migration**: Provide clear migration guide and training materials
3. **Feedback Collection**: Implement usage analytics to understand adoption

### Timeline Risks
1. **Scope Creep**: Use strict MVP definition and feature gates
2. **Testing Delays**: Allocate dedicated time for comprehensive testing
3. **Integration Issues**: Maintain clean separation between UI and core logic

## Success Metrics

### Technical Metrics
- [ ] PySide6 application builds and runs on all target platforms
- [ ] All Streamlit features replicated or improved upon
- [ ] Test coverage > 80% for new UI components
- [ ] Performance benchmarks meet or exceed Streamlit
- [ ] No critical bugs in production use

### User Experience Metrics
- [ ] User satisfaction rating > 4.0/5.0
- [ ] Task completion time reduced vs Streamlit
- [ ] Feature usage analytics show engagement
- [ ] Accessibility compliance score > 95%
- [ ] Cross-platform consistency score > 98%

### Adoption Metrics
- [ ] > 70% of users migrate to PySide6 within 3 months
- [ ] Positive feedback on professional feel and performance
- [ ] Reduced support requests for UI-related issues
- [ ] Increased usage of advanced features (multi-window, annotations)

## Rollback Plan

### Emergency Rollback (Critical Issues)
1. **Detection**: Automated monitoring detects critical failures
2. **Communication**: Immediate notification to all users
3. **Action**: Revert to Streamlit as primary interface
4. **Investigation**: Root cause analysis and fix planning
5. **Retry**: Implement fixes and redeploy

### Gradual Rollback (User Dissatisfaction)
1. **Monitoring**: Track user feedback and usage patterns
2. **Thresholds**: Define clear criteria for rollback decision
3. **Communication**: Transparent communication with users
4. **Transition**: Provide both interfaces during rollback period
5. **Analysis**: Understand reasons for dissatisfaction and address

## Documentation Updates

### User Documentation
- [ ] Update installation guide for PySide6 requirements
- [ ] Create PySide6-specific user guide
- [ ] Update screenshots and examples
- [ ] Add migration guide for existing users
- [ ] Document keyboard shortcuts and advanced features

### Developer Documentation
- [ ] PySide6 development setup guide
- [ ] Component architecture documentation
- [ ] Testing guidelines for desktop interface
- [ ] Contributing guidelines for UI development
- [ ] Performance optimization guide

### API Documentation
- [ ] Update interface references in API docs
- [ ] Document any changes to CLI behavior
- [ ] Update examples to show desktop interface

## Communication Plan

### Internal Communication
- **Team Updates**: Weekly progress reports during migration
- **Code Reviews**: Ensure all changes reviewed for PySide6 compatibility
- **Documentation**: Keep all docs updated as features are implemented

### External Communication
- **Release Notes**: Announce PySide6 as new primary interface
- **User Announcements**: Email/blog post about the change and benefits
- **Support Channels**: Update FAQ and troubleshooting guides
- **Feedback Collection**: Survey users on PySide6 experience

## Maintenance and Evolution

### Post-Migration Support
- [ ] Monitor PySide6 for updates and security patches
- [ ] Maintain compatibility with Qt versions
- [ ] Update dependencies regularly
- [ ] Performance monitoring and optimization

### Future Enhancements
- [ ] Plugin system for custom visualizations
- [ ] Advanced graph algorithms (force-directed layouts, clustering)
- [ ] Collaboration features (shared workspaces, comments)
- [ ] Integration with external tools (Obsidian, Zotero, etc.)
- [ ] Mobile companion app (using Qt for mobile)

## Conclusion

This migration plan provides a structured approach to transitioning Autoresearch from Streamlit to PySide6 while minimizing risk and ensuring a superior user experience. The PySide6 desktop interface will provide the professional, high-performance research environment that matches Autoresearch's local-first philosophy and target user needs.

**Key Success Factors:**
1. Thorough POC validation before full commitment
2. Gradual feature implementation with user feedback
3. Comprehensive testing across all platforms
4. Clear communication with users throughout the process
5. Maintaining CLI/API as reliable fallbacks during transition

The result will be a world-class research interface that differentiates Autoresearch in the market and provides users with the powerful, professional tools they need for serious research work.
