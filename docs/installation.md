# Installation

This guide explains how to install Autoresearch and manage optional features.

## Requirements

- Python 3.12 or newer (but below 4.0)
- `git` and build tools if compiling optional packages

## Minimal installation

The project can be installed with only the minimal optional dependencies:

```bash
pip install autoresearch[minimal]
```

This provides the CLI, API and knowledge graph without heavy NLP or UI packages. Optional features will be disabled when their dependencies are missing.

## Optional extras

Additional functionality is grouped into Poetry extras:

- `nlp` – language processing via spaCy, BERTopic and Transformers
- `parsers` – PDF and DOCX document ingestion
- `ui` – the reference Streamlit interface
- `vss` – DuckDB VSS extension for vector search
- `distributed` – distributed processing with Ray
- `full` – installs all optional extras

Install multiple extras separated by commas:

```bash
pip install "autoresearch[minimal,nlp,parsers]"
```

## Upgrading

To upgrade an existing installation run:

```bash
python scripts/upgrade.py
```

The helper script detects whether Poetry or pip is used. It runs
`poetry update autoresearch` when a `pyproject.toml` is present,
otherwise it falls back to `pip install -U autoresearch`.

The project follows semantic versioning. Minor releases within the same major version are backwards compatible. Check the [duckdb_compatibility.md](duckdb_compatibility.md) document for extension version notes.

