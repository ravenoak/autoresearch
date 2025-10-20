# PySide6 Layout Diagram

This document illustrates the layout and primary interactions of the PySide6
application using the current widget names.

```mermaid
graph TD
    MainWindow[Main Window]
    MenuBar[Menu Bar]
    ToolBar[Tool Bar]
    CentralStack[Central Stack]
    ConfigDock[Dock: ConfigEditor]
    SessionDock[Dock: SessionManager]
    ExportDock[Dock: ExportManager]

    MainWindow --> MenuBar
    MainWindow --> ToolBar
    MainWindow --> CentralStack
    MainWindow --> ConfigDock
    MainWindow --> SessionDock
    MainWindow --> ExportDock

    CentralStack --> QueryPanel[QueryPanel]
    CentralStack --> ResultsDisplay[ResultsDisplay]

    QueryPanel --> ConfigEditor[ConfigEditor]
    ConfigEditor --> SessionManager[SessionManager]
    SessionManager --> ResultsDisplay
    ResultsDisplay --> ExportManager[ExportManager]
```

```mermaid
sequenceDiagram
    participant User
    participant QueryPanel
    participant ConfigEditor
    participant SessionManager
    participant WorkerPool
    participant ResultsDisplay
    participant ExportManager

    User->>QueryPanel: Submit query request
    QueryPanel->>ConfigEditor: Collect execution parameters
    ConfigEditor->>SessionManager: Bundle session configuration
    SessionManager->>WorkerPool: Dispatch work item
    WorkerPool-->>SessionManager: Return completion payload
    SessionManager->>ResultsDisplay: Stream results and metrics data
    ResultsDisplay->>SessionManager: Request metrics refresh
    SessionManager-->>ResultsDisplay: Push updated metrics snapshot
    ResultsDisplay->>ExportManager: Signal export availability
    ExportManager-->>User: Offer export options
```

## Visual References

Supporting screenshots and wireframes will be stored under
`docs/images/pyside6_layout/` (placeholder). Add new assets to that directory
and reference them here once captures are available.
