# Installation

This guide explains how to install Autoresearch and manage optional features.

Autoresearch uses **uv** for dependency management. The examples below use `uv`.

## Requirements

- Python 3.12 or newer (but below 4.0)
- `git` and build tools if compiling optional packages

### Core dependencies

The following packages are required at the minimum versions listed. Each has
been verified to install successfully with `uv pip install`.

| Package | Minimum version |
| --- | --- |
| a2a-sdk | 0.3.0 |
| dspy-ai | 2.6.27 |
| duckdb | 1.3.0 |
| fastapi | 0.116.1 |
| fastmcp | 2.11.2 |
| httpx | 0.28.1 |
| kuzu | 0.11.1 |
| langchain-community | 0.3.27 |
| langchain-openai | 0.3.29 |
| langgraph | 0.6.4 |
| loguru | 0.7.3 |
| mcp[cli] | 1.12.4 |
| networkx | 3.5 |
| opentelemetry-api | 1.36.0 |
| opentelemetry-sdk | 1.36.0 |
| prometheus_client | 0.22.1 |
| psutil | 7.0.0 |
| pydantic | 2.11.7 |
| pydantic-settings | 2.10.1 |
| python-dotenv | 1.1.1 |
| rank-bm25 | 0.2.2 |
| rdflib | 7.1.4 |
| rdflib-sqlalchemy | 0.5.4 |
| requests | 2.32.4 |
| responses | 0.25.8 |
| rich | 14.1.0 |
| slowapi | 0.1.9 |
| structlog | 25.4.0 |
| tabulate | 0.9.0 |
| tinydb | 4.8.2 |
| typer | 0.16.0 |
| watchfiles | 1.1.0 |
| setuptools | 80.9.0 |
| owlrl | 7.1.4 |

## Development setup

Use `uv` to manage the environment when working from a clone:

```bash
# Create the virtual environment
uv venv
# Full feature set including development tools (required for CI)
uv pip install -e '.[full,parsers,git,llm,dev]'
# Lightweight install for quick smoke tests
# uv pip install -e '.[dev-minimal]'
```
Run `uv lock` whenever you change `pyproject.toml` to update `uv.lock` before syncing.
Selecting Python 3.11 results in an error similar to:
```
Because autoresearch requires Python >=3.12,<4.0 and the current Python is
3.11.*, no compatible version could be found.
```

Verify the environment by running:

```bash
task --version
uv pip list | grep flake8
uv run flake8 src tests
uv run mypy src
uv run pytest --version
uv run python -c "import importlib.metadata; print(importlib.metadata.version('pytest-bdd'))"
uv run python -c "import pydantic; print(pydantic.__version__)"
uv run pytest -q
uv run pytest tests/behavior
```

### Offline installation

To install without network access, pre-download the required packages and point the setup script at their locations:

```bash
export WHEELS_DIR=/path/to/wheels
export ARCHIVES_DIR=/path/to/archives
./scripts/setup.sh
```

`WHEELS_DIR` should contain wheel files (`*.whl`) and `ARCHIVES_DIR` should contain source archives (`*.tar.gz`). The setup script installs these caches with `uv pip --no-index` so dependencies resolve offline.

## Minimal installation

The project can be installed with only the minimal optional dependencies:

```bash
pip install autoresearch[minimal]
```

If you cloned the repository, run the setup helper. Omit the argument to
install all extras required for CI; use `dev-minimal` only for quick smoke
tests:

```bash
./scripts/setup.sh
# For a lightweight local setup:
# ./scripts/setup.sh dev-minimal
```

The helper ensures the lock file is refreshed and installs every optional
extra needed for the test suite. Tests normally rely on stubbed versions of
these extras, so running the suite without them is recommended. Extras such as
`slowapi` may enable real behaviour (like rate limiting) that changes how
assertions are evaluated. If you wish to revert to stub-only testing after
running the helper, reinstall using `uv sync --all-extras && uv pip install -e .`. Optional
features are disabled when their dependencies are missing. Specify extras
explicitly with pip to enable additional features, e.g. ``pip install "autoresearch[minimal,nlp]"``.

## Optional extras

Additional functionality is grouped into optional extras:

- `nlp` – language processing via spaCy and BERTopic
- `llm` – heavy dependencies like `sentence-transformers` and `transformers`
- `parsers` – PDF and DOCX document ingestion
- `ui` – the reference Streamlit interface
- `vss` – DuckDB VSS extension for vector search
- `distributed` – distributed processing with Ray
- `analysis` – Polars-based data analysis utilities
- `git` – local Git repository search support
- `full` – installs most extras (nlp, ui, vss, distributed, analysis)
  but omits `parsers` and `git`

Install multiple extras separated by commas:

```bash
pip install "autoresearch[minimal,nlp,parsers,git]"
```

## Upgrading

To upgrade an existing installation run:

```bash
python scripts/upgrade.py
```

The helper script installs or upgrades using `uv pip`. When a `pyproject.toml` is present it runs `uv pip install -U autoresearch`; otherwise it falls back to `pip install -U autoresearch`.

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
pip install -U "autoresearch[full,llm]"
```

## Troubleshooting optional package builds

Some optional extras such as `hdbscan` may compile from source when no
pre-built wheel is available for your platform. These builds can take a
long time or fail on low-memory machines.

- Install `gcc`, `g++` and the Python development headers beforehand.
- If compilation hangs or exhausts memory, set `HDBSCAN_NO_OPENMP=1` to
  disable OpenMP optimizations.
- Consider installing a pre-built wheel with `pip install hdbscan` prior
  to running `uv pip install -e '.[full,parsers,git,llm,dev]'`.
- You can omit heavy extras by specifying only the groups you need,
  e.g. `uv pip install -e '.[minimal]'` when rapid setup is more important
  than optional features.

