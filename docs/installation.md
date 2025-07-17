# Installation

This guide explains how to install Autoresearch and manage optional features.

## Requirements

- Python 3.12 or newer (but below 4.0)
- `git` and build tools if compiling optional packages

## Development setup

Use Poetry to manage the environment when working from a clone:

```bash
poetry env use $(which python3)
poetry lock --check || poetry lock
poetry install --with dev --all-extras
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

If you cloned the repository, run the setup helper instead:

```bash
./scripts/setup.sh
```

The helper ensures the lock file is refreshed and installs every optional
extra needed for the test suite. Optional features are disabled when their
dependencies are missing. Specify extras explicitly with pip to enable
additional features, e.g. ``pip install "autoresearch[minimal,nlp]"``.

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

Use pip extras when upgrading to ensure optional dependencies remain
installed. For example:
```bash
pip install -U "autoresearch[nlp,ui]"
```
The project follows semantic versioning. Minor releases within the same
major version are backwards compatible. Check the
[duckdb_compatibility.md](duckdb_compatibility.md) document for extension
version notes.

### Migrating from older releases

If you installed Autoresearch before ``0.1.0`` simply upgrade the base
package and reinstall any extras you require:
```bash
pip install -U "autoresearch[full]"
```

