# Installation

This guide explains how to install Autoresearch and manage optional features.

## Requirements

- Python 3.12 or newer (but below 4.0)
- `git` and build tools if compiling optional packages

## Development setup

Use Poetry to manage the environment when working from a clone:

```bash
poetry env use $(which python3)
poetry install --with dev
```

Verify the environment by running:

```bash
poetry run flake8 src tests
poetry run mypy src
poetry run pytest -q
poetry run pytest tests/behavior
```

## Minimal installation

The project can be installed with only the minimal optional dependencies:

```bash
pip install autoresearch[minimal]
```

If you cloned the repository, run the installer script instead:

```bash
python scripts/installer.py --minimal
```

This provides the CLI, API and knowledge graph without heavy NLP or UI packages.
Optional features will be disabled when their dependencies are missing.
Running ``scripts/installer.py`` without flags reads ``autoresearch.toml`` and
installs any extras required by the configuration. You can also specify extras
explicitly with the ``--extras`` flag, e.g. ``--extras nlp,ui``.

To install extras automatically according to your configuration, simply run:

```bash
python scripts/installer.py
```

Add ``--upgrade`` to update the base package and any detected extras.

## Optional extras

Additional functionality is grouped into Poetry extras:

- `nlp` – language processing via spaCy, BERTopic and Transformers
- `parsers` – PDF and DOCX document ingestion
- `ui` – the reference Streamlit interface
- `vss` – DuckDB VSS extension for vector search
- `distributed` – distributed processing with Ray
- `analysis` – Polars-based data analysis utilities
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

When using the installer script you can upgrade all packages with:

```bash
python scripts/installer.py --upgrade
```

The ``--upgrade`` flag installs any missing extras detected from your
configuration and then runs ``poetry update``. The project follows
semantic versioning. Minor releases within the same major version are
backwards compatible. Check the
[duckdb_compatibility.md](duckdb_compatibility.md) document for extension
version notes.

### Migrating from older releases

If you installed Autoresearch before ``0.1.0`` you may not have the
installer script available. Upgrade the base package and then run the
installer to pull in any new optional dependencies:

```bash
pip install -U autoresearch
python scripts/installer.py --upgrade
```

