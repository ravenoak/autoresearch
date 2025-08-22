# Installation

This guide is the canonical bootstrap reference for Autoresearch. It covers
the minimal developer workflow and links to helper scripts for specific
environments.

Autoresearch requires **Python 3.12 or newer**,
[**uv**](https://github.com/astral-sh/uv), and
[**Go Task**](https://taskfile.dev/) for Taskfile commands. **Install Go Task
before running any `task` commands** such as `task install`. After installing
Go Task and cloning the repository, bootstrap the environment and verify the
toolchain:

```bash
task install
uv run python scripts/check_env.py
```

This sequence installs the minimal development dependencies and checks that
**uv** and Go Task meet the version requirements.
The helper script automates additional setup:

- [`scripts/setup.sh`](../scripts/setup.sh) – full developer bootstrap

## Requirements

- Python 3.12 or newer (but below 4.0)
- `uv`
- Go Task
- `git` and build tools if compiling optional packages

### Go Task

Autoresearch uses [Go Task](https://taskfile.dev/) to run Taskfile commands.
Install it before invoking `task`:

```bash
# macOS
brew install go-task/tap/go-task

# Linux
curl -sSL https://taskfile.dev/install.sh | sh
```

After installation, initialize the environment:

```bash
task install
```

### Core dependencies

The following packages are required at the minimum versions listed. Each has
been verified to install successfully with `uv pip install`.

| Package | Minimum version |
| --- | --- |
| a2a-sdk | 0.3.0 |
| dspy-ai | 2.6.27 |
| duckdb | 1.3.0 |
| fastapi | 0.115.12 |
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

The table reflects minima validated for Python 3.12. Some packages use higher
pins than their upstream defaults to avoid compatibility issues, such as
`fastmcp>=2.11.2` and `watchfiles>=1.1.0`.

## Development setup

Install Go Task before running any `task` commands mentioned below.

Use `uv` to manage the environment when working from a clone:

```bash
# Install pinned dependencies for minimal development
uv sync --extra dev-minimal
# Activate the environment
source .venv/bin/activate
```

Run `task install` or `uv sync --extra dev-minimal` before executing tests to
ensure the minimal dependencies are available.

Add heavy extras on demand:

```bash
uv sync --extra ui
uv sync --extra nlp
```

After installing Go Task, pick a bootstrap method:

- `task install` – minimal setup
- [`scripts/setup.sh`](../scripts/setup.sh) – full developer toolchain

Run `uv lock` whenever you change `pyproject.toml` to update `uv.lock`
before syncing. Selecting Python 3.11 results in an error similar to:
```
Because autoresearch requires Python >=3.12,<4.0 and the current Python is
3.11.*, no compatible version could be found.
```

Verify the environment by running:

```bash
uv run python scripts/check_env.py
```

### Packaging verification

Build and validate distribution artifacts before publishing:

```bash
uv run python -m build
uv run python scripts/publish_dev.py --dry-run
```

If the DuckDB VSS extension cannot be downloaded,
`scripts/download_duckdb_extensions.py` reads `.env.offline` and uses
`VECTOR_EXTENSION_PATH` so the project works without vector search support.
`scripts/setup.sh` now writes a stub ``vss.duckdb_extension`` to the bundled
``extensions`` directory when no binary is available, ensuring tests and
``task check`` continue to run.

### Offline installation

To install without network access, pre-download the required packages and
point the setup script at their locations:

```bash
export WHEELS_DIR=/path/to/wheels
export ARCHIVES_DIR=/path/to/archives
./scripts/setup.sh
```

[`scripts/setup.sh`](../scripts/setup.sh) respects these variables.

`WHEELS_DIR` should contain wheel files (`*.whl`) and `ARCHIVES_DIR` should
contain source archives (`*.tar.gz`). The setup script installs these caches
with `uv pip --no-index` so dependencies resolve offline.

## Minimal installation

The project can be installed with only the minimal optional dependencies:

```bash
pip install autoresearch[minimal]
```

If you cloned the repository, run the appropriate setup helper:

```bash
./scripts/setup.sh
```

[`scripts/setup.sh`](../scripts/setup.sh) installs every optional extra needed
for development.

The helper ensures the lock file is refreshed and installs every optional
extra needed for the test suite. Tests normally rely on stubbed versions of
these extras, so running the suite without them is recommended. Extras such as
`slowapi` may enable real behaviour (like rate limiting) that changes how
  assertions are evaluated. If you wish to revert to stub-only testing after
  running the helper, reinstall using `uv sync --extra ui --extra nlp`.
Optional features are disabled when their dependencies are missing. Specify
extras explicitly with pip to enable additional features, e.g.
``pip install "autoresearch[minimal,nlp]"``.

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

The helper script installs or upgrades using `uv pip`. When a
`pyproject.toml` is present it runs `uv pip install -U autoresearch`;
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
pip install -U "autoresearch[full,llm]"
```

## Troubleshooting optional package builds

Some optional extras such as `hdbscan` may compile from source when no
pre-built wheel is available for your platform. These builds can take a
long time or fail on low-memory machines.

- Install `gcc`, `g++` and the Python development headers beforehand.
- If compilation hangs or exhausts memory, set `HDBSCAN_NO_OPENMP=1` to
  disable OpenMP optimizations.
- Consider installing a pre-built wheel with `pip install hdbscan` before
  running `uv sync`.
- You can omit heavy extras by syncing only the groups you need,
  e.g. `uv sync --extra dev-minimal` when rapid setup is more important
  than optional features.

