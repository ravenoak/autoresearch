# UX Architecture Diagrams

This document provides architecture diagrams highlighting the UX components of the Autoresearch system.

## Overall Architecture with UX Components

```mermaid
graph TD
    User[User] --> CLI[CLI Interface]
    User --> GUI[Streamlit GUI]
    User --> A2A[A2A Interface]
    User --> MCP[MCP Interface]
    
    CLI --> Core[Core System]
    GUI --> Core
    A2A --> Core
    MCP --> Core
    
    Core --> Agents[Agent System]
    Core --> Storage[Storage System]
    Core --> Search[Search System]
    
    subgraph "UX Components"
        CLI
        GUI
        A2A
        MCP
        OutputFormat[Output Formatting]
        ErrorHandling[Error Handling]
        ProgressIndicators[Progress Indicators]
    end
    
    CLI --> OutputFormat
    GUI --> OutputFormat
    A2A --> OutputFormat
    MCP --> OutputFormat
    
    CLI --> ErrorHandling
    GUI --> ErrorHandling
    A2A --> ErrorHandling
    MCP --> ErrorHandling
    
    CLI --> ProgressIndicators
    GUI --> ProgressIndicators
```

## CLI Interface Components

```mermaid
graph TD
    User[User] --> CLI[CLI Interface]
    
    CLI --> QueryCommand[Query Command]
    CLI --> ConfigCommand[Config Command]
    CLI --> MonitorCommand[Monitor Command]
    CLI --> GuiCommand[GUI Command]
    ConfigCommand --> LocalFileSetup[Configure Local File Backend]
    ConfigCommand --> GitRepoSetup[Configure Git Backend]
    
    QueryCommand --> OutputFormat[Output Formatting]
    ConfigCommand --> OutputFormat
    MonitorCommand --> OutputFormat
    
    QueryCommand --> ProgressIndicators[Progress Indicators]
    
    subgraph "Accessibility Features"
        ColorAlternatives[Color Alternatives]
        SymbolicIndicators[Symbolic Indicators]
        ScreenReaderSupport[Screen Reader Support]
    end
    
    OutputFormat --> ColorAlternatives
    OutputFormat --> SymbolicIndicators
    ProgressIndicators --> ScreenReaderSupport
```

## Streamlit GUI Components

```mermaid
graph TD
    User[User] --> GUI[Streamlit GUI]
    
    GUI --> QueryInput[Query Input]
    GUI --> ResultsTabs[Results Tabs]
    GUI --> ConfigEditor[Config Editor]
    ConfigEditor --> LocalFileSetupGUI[Configure Local File Backend]
    ConfigEditor --> GitRepoSetupGUI[Configure Git Backend]
    GUI --> MetricsDashboard[Metrics Dashboard]

    MetricsDashboard --> ProgressMetrics[Progress Metrics]

    ResultsTabs --> AnswerTab[Answer Tab]
    ResultsTabs --> ReasoningTab[Reasoning Tab]
    ResultsTabs --> CitationsTab[Citations Tab]
    ResultsTabs --> KnowledgeGraphTab[Knowledge Graph Tab]
    ResultsTabs --> TraceTab[Trace Tab]
    
    subgraph "Accessibility Features"
        KeyboardNavigation[Keyboard Navigation]
        ScreenReaderSupport[Screen Reader Support]
        HighContrastMode[High Contrast Mode]
    end
    
    GUI --> KeyboardNavigation
    GUI --> ScreenReaderSupport
    GUI --> HighContrastMode
```

## Cross-Modal Integration

```mermaid
graph TD
    CLI[CLI Interface] --> SharedConfig[Shared Configuration]
    GUI[Streamlit GUI] --> SharedConfig
    A2A[A2A Interface] --> SharedConfig
    MCP[MCP Interface] --> SharedConfig
    
    CLI --> SharedQueryHistory[Shared Query History]
    GUI --> SharedQueryHistory
    
    CLI --> ConsistentOutput[Consistent Output Format]
    GUI --> ConsistentOutput
    A2A --> ConsistentOutput
    MCP --> ConsistentOutput
    
    CLI --> ConsistentErrors[Consistent Error Handling]
    GUI --> ConsistentErrors
    A2A --> ConsistentErrors
    MCP --> ConsistentErrors
```

## User Flow Diagram

```mermaid
graph TD
    Start[Start] --> ChooseInterface[Choose Interface]
    
    ChooseInterface --> UseCLI[Use CLI]
    ChooseInterface --> UseGUI[Use GUI]
    ChooseInterface --> UseA2A[Use A2A]
    ChooseInterface --> UseMCP[Use MCP]
    
    UseCLI --> EnterCLIQuery[Enter Query in CLI]
    UseGUI --> EnterGUIQuery[Enter Query in GUI]
    UseA2A --> SendA2ARequest[Send A2A Request]
    UseMCP --> SendMCPRequest[Send MCP Request]
    
    EnterCLIQuery --> ViewCLIResults[View Results in CLI]
    EnterGUIQuery --> ViewGUIResults[View Results in GUI]
    SendA2ARequest --> ReceiveA2AResponse[Receive A2A Response]
    SendMCPRequest --> ReceiveMCPResponse[Receive MCP Response]
    
    ViewCLIResults --> SwitchToGUI[Switch to GUI]
    SwitchToGUI --> ViewHistoryInGUI[View History in GUI]
    ViewHistoryInGUI --> RerunQueryInGUI[Rerun Query in GUI]
    
    ViewGUIResults --> ExportResults[Export Results]
    ViewGUIResults --> ModifyConfig[Modify Configuration]
    ModifyConfig --> ConfigureLocalFiles[Set Local File Backend]
    ModifyConfig --> ConfigureGitRepo[Set Git Backend]
    ModifyConfig --> EnterGUIQuery
```

These diagrams provide a high-level overview of the UX architecture of the Autoresearch system, highlighting the different interfaces, their components, and how they interact with each other and the core system.