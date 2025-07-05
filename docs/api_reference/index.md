# API Reference

This section provides detailed API documentation for the Autoresearch project, generated automatically from docstrings in the source code.

## Overview

The Autoresearch API is organized into several modules:

- **Agents**: Classes and functions for implementing and managing agents
- **Orchestration**: Components for coordinating agent execution
- **Storage**: Storage and persistence functionality
- **LLM**: Language model integration and adapters
- **Search**: Search functionality and backends
- **Config**: Configuration management
The HTTP API also exposes REST endpoints. Use `DELETE /query/{query_id}` to cancel an asynchronous query.


## Using the API

The API documentation provides detailed information about classes, methods, and functions, including:

- Method signatures with parameter types and return types
- Docstrings with descriptions of functionality
- Parameter descriptions
- Return value descriptions
- Exception information

## Example

Here's a simple example of using the Autoresearch API programmatically:

```python
from autoresearch.orchestration import Orchestrator
from autoresearch.config import ConfigLoader

# Load configuration
config = ConfigLoader.load()

# Create an orchestrator
orchestrator = Orchestrator()

# Run a query
response = orchestrator.run_query("What is the impact of climate change on biodiversity?", config)

# Print the response
print(response.answer)
```

## Module Documentation

For detailed documentation of each module, see the corresponding pages in this section:

- [Agents](agents.md): Agent base classes, specialized agents, and agent registry
- [Orchestration](orchestration.md): Orchestrator, reasoning modes, and state management
- [Storage](storage.md): Storage manager, backends, and persistence
- [LLM](llm.md): LLM adapters, registry, and token counting
- [Search](search.md): Search functionality and backends
- [Config](config.md): Configuration loading and management
- [Distributed](distributed.md): Executors and helper utilities for distributed execution

