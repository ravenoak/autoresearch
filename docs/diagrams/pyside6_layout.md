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

Supporting screenshots and wireframes will be stored under
`docs/images/pyside6_layout/` (placeholder). Add new assets to that directory
and reference them here once captures are available.
