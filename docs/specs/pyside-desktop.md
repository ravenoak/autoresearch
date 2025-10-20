# PySide6 Desktop Interface

## Overview

AutoresearchMainWindow provides the desktop shell for the PySide6
application. The window embeds a vertical splitter with QueryPanel input on
top and ResultsDisplay tabs below, while dock widgets expose configuration,
session history, and export tools. Supporting widgets, including
KnowledgeGraphView and MetricsDashboard, extend the interface with
visualisation, accessibility, and runtime telemetry.

Phase 1 wireframes capture the baseline layout and running-query feedback in
[Figure 1](../diagrams/pyside6_layout.md#visual-references) so engineering,
design, and product teams can validate keyboard-first submission, accessible
configuration editing, and export gating cues together.

## Algorithms

- AutoresearchMainWindow bootstraps orchestrator dependencies, wires signals,
and maintains a polling timer that refreshes status-bar metrics from the
active orchestrator metrics provider.
- QueryPanel emits query_submitted events after validating text input and
collecting reasoning parameters, ensuring configuration overrides flow back to
the main window before execution.
- ResultsDisplay renders QueryResponse payloads by delegating Markdown output
to OutputFormatter, normalising citations for accessibility, rendering
knowledge graphs via KnowledgeGraphView, and relaying metrics to
MetricsDashboard.
- KnowledgeGraphView normalises node and edge data, applies a circular layout
fallback, and uses optional NetworkX layouts when available before rendering a
Qt graphics scene with export actions.
- MetricsDashboard streams metrics snapshots from either explicit updates or a
bound provider, smoothing time-series data, driving Matplotlib charts when
available, and keeping an accessible textual summary as a fallback.

## Invariants

- The main window maintains QueryPanel, ResultsDisplay, and a status bar with
CPU, memory, and token labels so the core workflow remains available even when
optional dependencies are missing.
- Dock widgets for configuration, sessions, and exports remain accessible via
View menu toggle actions stored on AutoresearchMainWindow to prevent garbage
collection.
- Query execution toggles is_query_running, displays an indeterminate progress
  bar, disables QueryPanel inputs via the busy state, and resets status
  messaging regardless of success, failure, or user cancellation paths.
- ResultsDisplay preserves tab instances and clears state-specific widgets when
no data is present so subsequent queries render correctly.
- KnowledgeGraphView and MetricsDashboard fall back to textual summaries when
optional libraries such as NetworkX or Matplotlib are unavailable, preserving
usability.

## Optional Dependency Fallbacks

- Answer Tab — When Qt WebEngine cannot be imported the ResultsDisplay swaps the
  embedded QWebEngineView for a QTextBrowser paired with a QLabel notice so the
  formatted answer still renders without scripting support. Users keep external
  link access while being prompted to install PySide6-WebEngine for full
  interactivity.
- Knowledge Graph — KnowledgeGraphView detects missing NetworkX at import time
  and disables non-circular layouts while keeping the textual detail panel,
  export buttons, and a placeholder message so graph data remains accessible as
  node and edge summaries.
- Metrics Dashboard — The metrics stack instantiates Matplotlib canvases only
  when ``Figure`` and ``FigureCanvasQTAgg`` import successfully. Otherwise, it
  pins the stacked widget to the textual summary view, disables the toggle
  button, and annotates the screen-reader description to clarify that charts are
  unavailable until Matplotlib is installed.

## Proof Sketch

Signal-slot bindings connect QueryPanel to AutoresearchMainWindow, which
spawns background workers for orchestrator queries and marshals results back to
the GUI thread. Status timers and export updates reuse the most recent metrics
payload to keep UI labels synchronised even when live polling fails. Each
dock widget encapsulates its own state management, and the tests confirm that
initialisation, updates, and fallback paths emit expected signals and text.

## Simulation Expectations

Tests under tests/ui/desktop/ exercise component behaviour with QtBot, validate
metrics refresh and fallback states, simulate knowledge graph rendering, and
assert integration wiring in AutoresearchMainWindow. These scenarios cover
signal emission, layout persistence, accessibility toggles, and export button
management across realistic UI lifecycles.

## Traceability

- Modules
  - [src/autoresearch/ui/desktop/main_window.py][m1]
  - [src/autoresearch/ui/desktop/query_panel.py][m2]
  - [src/autoresearch/ui/desktop/results_display.py][m3]
  - [src/autoresearch/ui/desktop/config_editor.py][m4]
  - [src/autoresearch/ui/desktop/session_manager.py][m5]
  - [src/autoresearch/ui/desktop/export_manager.py][m6]
  - [src/autoresearch/ui/desktop/knowledge_graph_view.py][m7]
  - [src/autoresearch/ui/desktop/metrics_dashboard.py][m8]
  - [src/autoresearch/ui/desktop/main.py][m9]
- Tests
  - [tests/ui/desktop/test_component_smoke.py][t1] (**T-UI-001**)
  - [tests/ui/desktop/test_desktop_integration.py][t2] (**T-UI-004**)
  - [tests/ui/desktop/test_query_panel.py][t3] (**T-UI-002**)
  - [tests/ui/desktop/test_results_display.py][t4] (**T-UI-003**)

### Test ID Legend

- **T-UI-001** — Smoke checks for widget fallbacks and export readiness. See
  [tests/ui/desktop/test_component_smoke.py][t1].
- **T-UI-002** — Query submission ergonomics and keyboard traversal. See
  [tests/ui/desktop/test_query_panel.py][t3].
- **T-UI-003** — Results rendering, citations, and telemetry surfaces. See
  [tests/ui/desktop/test_results_display.py][t4].
- **T-UI-004** — End-to-end desktop orchestration flow. See
  [tests/ui/desktop/test_desktop_integration.py][t2].

[m1]: ../../src/autoresearch/ui/desktop/main_window.py
[m2]: ../../src/autoresearch/ui/desktop/query_panel.py
[m3]: ../../src/autoresearch/ui/desktop/results_display.py
[m4]: ../../src/autoresearch/ui/desktop/config_editor.py
[m5]: ../../src/autoresearch/ui/desktop/session_manager.py
[m6]: ../../src/autoresearch/ui/desktop/export_manager.py
[m7]: ../../src/autoresearch/ui/desktop/knowledge_graph_view.py
[m8]: ../../src/autoresearch/ui/desktop/metrics_dashboard.py
[m9]: ../../src/autoresearch/ui/desktop/main.py
[t1]: ../../tests/ui/desktop/test_component_smoke.py
[t2]: ../../tests/ui/desktop/test_desktop_integration.py
[t3]: ../../tests/ui/desktop/test_query_panel.py
[t4]: ../../tests/ui/desktop/test_results_display.py
