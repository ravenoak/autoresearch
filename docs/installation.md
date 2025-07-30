# Installation

This guide explains how to install Autoresearch and manage optional features.

Autoresearch uses **uv** for dependency management. The examples below use `uv`.

## Requirements

- Python 3.12 or newer (but below 4.0)
- `git` and build tools if compiling optional packages

## Development setup

Use `uv` to manage the environment when working from a clone:

```bash
# Create the virtual environment
uv venv
# Full feature set including development tools
uv pip install -e '.[full,llm,dev]'
# Lightweight install for CI or quick tests
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
uv pip list | grep flake8
uv run flake8 src tests
uv run mypy src
uv run pytest -q
uv run pytest tests/behavior
```

## Minimal installation

The project can be installed with only the minimal optional dependencies:

```bash
pip install autoresearch[minimal]
```

If you cloned the repository, run the setup helper. Pass `dev-minimal` for a
lightweight install or omit the argument for the full feature set:

```bash
./scripts/setup.sh dev-minimal
# ./scripts/setup.sh
```

The helper ensures the lock file is refreshed and installs every optional
extra needed for the test suite. Tests normally rely on stubbed versions of
these extras, so running the suite without them is recommended. Extras such as
`slowapi` may enable real behaviour (like rate limiting) that changes how
assertions are evaluated. If you wish to revert to stub-only testing after
running the helper, reinstall using `uv pip install -e '.[full,llm,dev]'`. Optional
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
- `full` – installs all optional extras except `llm`

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
  to running `uv pip install -e '.[full,llm,dev]'`.
- You can omit heavy extras by specifying only the groups you need,
  e.g. `uv pip install -e '.[minimal]'` when rapid setup is more important
  than optional features.

