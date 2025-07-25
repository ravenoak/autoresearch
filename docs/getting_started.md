# Getting Started

This guide walks you through installing the project dependencies and running your first search.

## System Architecture

Autoresearch uses a modular architecture with several key components. The PlantUML diagram for the overall system architecture is available at `docs/diagrams/system_architecture.puml`.

- The system consists of:
- **Client Interfaces**: CLI, API, Monitor, and FastMCP
- **Core Components**: Orchestrator, ConfigLoader, Error Hierarchy, Metrics, and Tracing
- **Agents**: Synthesizer, Contrarian, and Fact-Checker
- **LLM Integration**: Adapters for different LLM backends
- **Storage & Search**: Hybrid storage system with vector search
- **Output Formatting**: Formatting and synthesis of results

## Installation

Use `uv venv` and `uv pip install -e '.[full,dev]'` to set up a development environment:

```bash
uv venv
uv pip install -e '.[full,dev]'
```

`hdbscan` is built from source and needs compilation tools. Install `gcc`, `g++`,
and the Python development headers first. On Debian/Ubuntu run:

```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

If OpenMP support causes build issues you can disable it with:

```bash
export HDBSCAN_NO_OPENMP=1
```

Alternatively install via pip:

```bash
pip install -e .
```

## First search

Run a search from the command line:

```bash
autoresearch search "What is quantum computing?"
```

## Local file and Git search

Enable local search backends in `autoresearch.toml`:

```toml

[search]
backends = ["serper", "local_file", "local_git"]


[search.local_file]
path = "/path/to/docs"
file_types = ["md", "pdf", "docx", "txt"]

[search.local_git]
repo_path = "/path/to/repo"
branches = ["main"]
history_depth = 50
```

Local search results are merged with those from web backends so your documents
and code appear alongside external sources. PDF and DOCX files are parsed
automatically and Git commit diffs are indexed so code history shows up in
results. All sources are ranked together using BM25 and embedding similarity.

Then query your directory or repository just like any other search:

```bash
autoresearch search "neural networks in docs"
```

## MCP Interface

Autoresearch also exposes a **FastMCP** server so other agents can use it as a
tool. Start the server with:

```bash
autoresearch serve
```

Send a query using the provided client helper:

```python
from autoresearch.mcp_interface import query

result = query("What is the capital of France?")
print(result["answer"])
```

