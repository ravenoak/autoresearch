# Getting Started

This guide walks you through installing the project dependencies and running your first search.

## System Architecture

Autoresearch uses a modular architecture with several key components:

![System Architecture](diagrams/system_architecture.png)

The system consists of:
- **Client Interfaces**: CLI, API, and Monitor
- **Core Components**: Orchestrator, ConfigLoader, Error Hierarchy, Metrics, and Tracing
- **Agents**: Synthesizer, Contrarian, and Fact-Checker
- **LLM Integration**: Adapters for different LLM backends
- **Storage & Search**: Hybrid storage system with vector search
- **Output Formatting**: Formatting and synthesis of results

## Installation

Use `poetry install` to set up a development environment:

```bash
poetry install
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
