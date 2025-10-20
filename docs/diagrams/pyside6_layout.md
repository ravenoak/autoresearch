# PySide6 Layout Diagram

This document illustrates the layout and primary interactions of the PySide6
application using the current widget names.

The ResultsDisplay tab stack now incorporates a structured search results pane
adjacent to the narrative answer, providing a dedicated table for ranked hits
alongside the existing citations, knowledge graph, and metrics views.

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

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running: query submitted / start timer
    Running --> Succeeded: worker done / stop timer
    Running --> Cancelling: confirm cancel / stop timer
    Cancelling --> Failed: worker error / show dialog
    Cancelling --> Succeeded: teardown clean / reset flags
    Succeeded --> Idle: reset status, focus query panel
    Failed --> Idle: reset status, focus query panel
```

## Visual References

![Phase 1 initial layout wireframe](../images/pyside6_layout/phase1_initial_layout.svg)
*Figure 1: Baseline window composition showing QueryPanel and dock widgets
required for the Phase 1 stories about keyboard-first submission, accessible
configuration controls, and results parity.*

![Phase 1 running query wireframe](../images/pyside6_layout/phase1_running_query.svg)
*Figure 2: Running-query feedback emphasising progress, disabled controls, and
export gating tied to Phase 1 cancellation and status feedback stories.*

![Phase 1 cancel confirmation wireframe](../images/pyside6_layout/phase1_cancel_confirmation.svg)
*Figure 3: Cancellation prompt illustrating the modal copy, destructive
confirmation button, and persistent busy overlay used before worker teardown.*

![Phase 1 error dialog wireframe](../images/pyside6_layout/phase1_error_dialog.svg)
*Figure 4: Error state showing the critical dialog, status-bar reset, and
export gating after a cancellation surfaces a worker failure.*
