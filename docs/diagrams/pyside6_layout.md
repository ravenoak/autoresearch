# PySide6 Layout Diagram

This document illustrates the layout and primary interactions of the PySide6
application using the current widget names.

```mermaid
graph TD
    AutoresearchMainWindow[AutoresearchMainWindow]
    QueryPanel[QueryPanel]
    ResultsDisplay[ResultsDisplay]
    ConfigEditor[ConfigEditor]
    SessionManager[SessionManager]
    ExportManager[ExportManager]

    AutoresearchMainWindow -->|central splitter| QueryPanel
    AutoresearchMainWindow -->|central splitter| ResultsDisplay
    AutoresearchMainWindow -->|dock| ConfigEditor
    AutoresearchMainWindow -->|dock| SessionManager
    AutoresearchMainWindow -->|dock| ExportManager

    QueryPanel --> ConfigEditor
    ConfigEditor --> SessionManager
    SessionManager --> ResultsDisplay
    ResultsDisplay --> ExportManager
```

```mermaid
sequenceDiagram
    participant User
    participant QueryPanel
    participant AutoresearchMainWindow
    participant QThreadPool
    participant QueryWorker
    participant ResultsDisplay
    participant SessionManager
    participant ExportManager

    User->>QueryPanel: Submit query request
    QueryPanel->>AutoresearchMainWindow: emit query_submitted(query)
    AutoresearchMainWindow->>AutoresearchMainWindow: Merge runtime configuration
    AutoresearchMainWindow->>QThreadPool: start(QueryWorker)
    QThreadPool->>QueryWorker: run query with config context
    QueryWorker-->>AutoresearchMainWindow: Deliver QueryResponse payload
    AutoresearchMainWindow->>ResultsDisplay: display_results(result)
    AutoresearchMainWindow->>SessionManager: add_session(metadata)
    AutoresearchMainWindow->>AutoresearchMainWindow: _refresh_status_metrics()
    AutoresearchMainWindow->>ExportManager: set_available_exports(exports)
    ExportManager-->>User: Present export choices
```

## Visual References

![Phase 1 initial layout wireframe](../images/pyside6_layout/phase1_initial_layout.svg)
*Figure 1: Baseline window composition showing QueryPanel and dock widgets
required for the Phase 1 stories about keyboard-first submission, accessible
configuration controls, and results parity.*

![Phase 1 running query wireframe](../images/pyside6_layout/phase1_running_query.svg)
*Figure 2: Running-query feedback emphasising progress, disabled controls, and
export gating tied to Phase 1 cancellation and status feedback stories.*
