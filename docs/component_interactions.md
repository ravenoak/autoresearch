# Component Interactions

This document explains the interactions between the various components of the Autoresearch system, as illustrated in the architecture diagrams in the `docs/diagrams` directory.

## System Architecture Overview

The Autoresearch system is composed of several interconnected components that work together to provide a comprehensive research assistant. The system architecture is organized into the following main areas:

1. Client Interfaces
2. Core Components
3. Agents
4. LLM Integration
5. Storage & Search
6. Output Formatting

![System Architecture](diagrams/system_architecture.png)

## Key Component Interactions

### User Interaction Flow

1. **User → Client Interfaces**: Users interact with the system through several interfaces:
   - Command Line Interface (CLI)
   - HTTP API (FastAPI)
   - A2A API
   - MCP Interface
   - Streamlit GUI
   - Interactive Monitor

2. **Client Interfaces → Orchestrator**: All client interfaces forward user queries to the Orchestrator, which is the central coordination component.

3. **Orchestrator → ConfigLoader**: The Orchestrator loads configuration settings from the ConfigLoader, which manages the system's configuration.

### Agent Execution Flow

1. **Orchestrator → AgentFactory**: The Orchestrator requests agent instances from the AgentFactory.

2. **AgentFactory → AgentRegistry**: The AgentFactory uses the AgentRegistry to look up agent classes by name.

3. **AgentFactory → Agent**: The AgentFactory creates and returns agent instances to the Orchestrator.

4. **Orchestrator → Agent**: The Orchestrator executes agents in the appropriate sequence based on the reasoning mode:
   - In dialectical mode: Synthesizer → Contrarian → FactChecker
   - In direct mode: Synthesizer only
   - In chain-of-thought mode: Synthesizer repeatedly

5. **Agent → LLMAdapters**: Agents use LLM adapters to generate responses from language models.

6. **LLMAdapters → LLMRegistry**: LLM adapters are obtained from the LLM registry based on the configured backend.

7. **LLMAdapters → TokenCounting**: Token usage is tracked for monitoring and budgeting purposes.

### Data Flow

1. **Orchestrator → StorageManager**: The Orchestrator persists claims (research findings) to the StorageManager.

2. **StorageManager → Storage Backends**: The StorageManager distributes data to various storage backends:
   - NetworkX Graph: For in-memory graph representation
   - DuckDB Store: For structured data storage
   - RDFLib Store: For RDF data interchange
   - TinyDB Cache: For caching

3. **Agent → Search**: Agents can perform external searches to gather information.

4. **Search → VectorSearch**: Vector search capabilities enhance search precision through semantic similarity.

5. **Orchestrator → OutputFormatter**: The Orchestrator formats the final results using the OutputFormatter.

6. **OutputFormatter → Synthesis**: The OutputFormatter uses the Synthesis component to build coherent answers.

## Detailed Component Interactions

### Orchestration System

The Orchestrator is the central coordination component that manages the execution of agents and the flow of data through the system:

```
User → Client Interface → Orchestrator → Agents → LLM → Storage → Output → User
```

Key interactions:
- Loads configuration from ConfigLoader
- Records metrics through Metrics Collector
- Traces execution through Tracing
- Handles errors through Error Hierarchy
- Coordinates agent execution
- Persists claims to storage
- Formats output for presentation

### Agent System

The agent system is responsible for processing queries and generating research findings:

```
Orchestrator → AgentFactory → AgentRegistry → Agent → LLMAdapters → Response
```

Key interactions:
- AgentFactory creates agent instances
- Agents use mixins for common functionality
- Agents generate prompts from templates
- Agents execute queries using LLM adapters
- Agents return structured results to the Orchestrator

### Storage System

The storage system persists research findings and enables knowledge retrieval:

```
Orchestrator → StorageManager → [NetworkX, DuckDB, RDFLib, TinyDB]
```

Key interactions:
- StorageManager validates and processes claims
- NetworkX stores graph relationships
- DuckDB stores structured data
- RDFLib stores semantic data
- TinyDB provides caching
- Vector search enables semantic retrieval

#### File and Git Backends

The **LocalFileBackend** and **GitBackend** extend the search pipeline with local
sources. The Orchestrator invokes the Search module, which uses the
FileLoader and GitRepoIndexer to crawl directories and repositories. Retrieved
snippets flow back to the Orchestrator and are persisted by the StorageManager.
The updated *Storage & Search* and *System Architecture* diagrams illustrate
this interaction chain:
Orchestrator → Search → FileLoader/GitRepoIndexer → StorageManager.

## Component Interaction Scenarios

### Query Execution Scenario

1. User submits a query through the CLI
2. CLI forwards the query to the Orchestrator
3. Orchestrator loads configuration from ConfigLoader
4. Orchestrator initializes metrics and tracing
5. Orchestrator creates a QueryState to track the query's progress
6. Orchestrator determines the reasoning mode and agent sequence
7. For each agent in the sequence:
   a. Orchestrator gets the agent from AgentFactory
   b. Agent generates a prompt using templates
   c. Agent executes the prompt using LLM adapters
   d. Agent returns results to Orchestrator
   e. Orchestrator persists results to StorageManager
8. Orchestrator formats the final results using OutputFormatter
9. CLI presents the formatted results to the user

### Error Handling Scenario

1. User submits a query that causes an error during agent execution
2. Agent raises an exception
3. Orchestrator catches the exception through the Error Hierarchy
4. Orchestrator logs the error and updates metrics
5. Orchestrator attempts to recover or gracefully degrade
6. If recovery is possible, Orchestrator continues execution
7. If recovery is not possible, Orchestrator returns an error response
8. Client interface presents the error to the user

### Configuration Change Scenario

1. User modifies the configuration file
2. ConfigLoader detects the change through file watching
3. ConfigLoader reloads the configuration
4. ConfigLoader notifies components of the configuration change
5. Components adapt to the new configuration settings
6. Subsequent queries use the updated configuration

## Extending Component Interactions

The Autoresearch system is designed to be extensible. Here are some ways to extend component interactions:

1. **New Agent Types**: Create new agent classes that inherit from the base Agent class and register them with the AgentRegistry.

2. **Custom LLM Adapters**: Implement new LLM adapters to support different language model providers and register them with the LLMRegistry.

3. **Alternative Storage Backends**: Create new storage backends and integrate them with the StorageManager.

4. **Custom Output Formatters**: Implement new output formatting templates or strategies.

5. **Additional Client Interfaces**: Create new client interfaces that interact with the Orchestrator.

## Conclusion

The component interactions in the Autoresearch system are designed to be modular, extensible, and robust. By understanding these interactions, developers can effectively extend and customize the system to meet specific research needs.

For more detailed information about specific components, refer to the architecture diagrams in the `docs/diagrams` directory and the corresponding source code.
