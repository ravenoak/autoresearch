# Autoresearch

Autoresearch is a local-first research assistant that coordinates multiple agents to
produce evidence-backed answers. It uses a dialectical reasoning process and stores all
data in local databases so that searches and knowledge graphs remain on your machine.
The project is built around a modular Python package located under `src/autoresearch/`.
CLI utilities are provided via Typer and the HTTP API is powered by FastAPI.

**Note:** [docs/installation.md](docs/installation.md) is the authoritative
source for environment setup and optional features.

For orchestrator state transitions and API contracts see
[docs/orchestrator_state.md](docs/orchestrator_state.md).

Concurrency guarantees for agent communication are detailed in
[docs/specs/a2a-interface.md](docs/specs/a2a-interface.md), which includes a
proof sketch and an event-driven simulation
([scripts/a2a_concurrency_sim.py](scripts/a2a_concurrency_sim.py)).

## Prerequisites

Install these binaries and ensure they are on your `PATH`:

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 0.7.0+
- [Go Task](https://taskfile.dev/)

Run `uv run python scripts/check_env.py` to confirm they are available. The
script exits with an error when Go Task is missing and suggests installing it
with `scripts/setup.sh` or your package manager. If a tool or package is
reported missing, rerun `task install` or sync optional extras with
`uv sync --extra <name>`. Run the setup script and verify Go Task with
`task --version`:

```bash
./scripts/setup.sh
source .venv/bin/activate
export PATH="$PATH:$(pwd)/.venv/bin"
task --version
task check
```

`scripts/setup.sh` verifies the Python version, installs Go Task when needed,
confirms `uv` is functional, and syncs the `dev-minimal` and `test` extras. It
exits with an error if a tool is missing or the dependency sync fails.

To install a system-wide Go Task binary instead, run:

```bash
curl -sSL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin
# macOS: brew install go-task/tap/go-task
```

Optional extras provide features such as NLP, a UI, or distributed
processing. Install them on demand with `uv sync --extra <name>`, `task
install EXTRAS="<name>"`, or `pip install "autoresearch[<name>]"`.

### Enabling heavy extras

`task verify` syncs only the `dev-minimal`, `dev`, and `test` extras.
Heavy groups such as `nlp`, `distributed`, `analysis`, and `llm` require
additional dependencies and must be enabled explicitly:

```bash
EXTRAS="nlp distributed" task verify
```

Use the same `EXTRAS` flag with `task install` to sync them for local
development.

A running Redis server is needed only for the `[distributed]` extra or tests
tagged `requires_distributed`. The test suite's `redis_client` fixture connects
to a local server or starts a lightweight `fakeredis` instance. When neither
service is available those scenarios are skipped. Run the distributed tests
with:

```bash
uv run pytest -m requires_distributed -q
```

To bootstrap a Python 3.12+ environment with the minimal development and
test extras run the install task and verify the Go Task binary:

```bash
task install
task --version
source .venv/bin/activate
```

If `task --version` fails, follow the manual setup below to run tests with
`uv`. This syncs the `dev-minimal` and `test` extras. Include heavy groups
only when required:

```bash
task install EXTRAS="nlp distributed"
uv sync --extra nlp --extra distributed
```

To install the `[test]` extras directly without Go Task and download the DuckDB
VSS extension, run:

```bash
uv pip install -e ".[test]"
uv run scripts/download_duckdb_extensions.py --output-dir ./extensions
```

### Manual setup without Go Task

`scripts/setup.sh` installs Go Task automatically. If you cannot use the
bootstrap script, install the test extras manually:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
uv run scripts/download_duckdb_extensions.py --output-dir ./extensions
uv run pytest tests/unit/test_version.py -q
```

The `[test]` extra installs dependencies like `pytest-bdd`, which `task check`
expects for quick smoke tests. Install it before `pytest` to mirror the DuckDB
setup performed by `scripts/setup.sh` and let `uv run pytest` succeed without
`task`.

Run `task check` for linting, type checks, and quick smoke tests. It syncs the
`dev-minimal` and `test` extras and exercises a small unit subset
(`test_version` and `test_cli_help`) for fast feedback. `task verify` runs the
full suite and installs only the `dev-minimal`, `dev`, and `test` extras.
Pass `EXTRAS="distributed analysis"` or similar when invoking the command to
include heavy groups.

For current capabilities and known limitations see
[docs/release_notes.md](docs/release_notes.md).

## Roadmap

As of **September 9, 2025**, Autoresearch is in the **Development** phase
preparing for the upcoming **0.1.0** release. The version is defined in
`autoresearch.__version__` and mirrored in `pyproject.toml`, but it has
**not** been published yet. The first official release was originally
planned for **July 20, 2025**, but the schedule slipped. An
**0.1.0a1** preview is targeted for **September 15, 2026**, with
the final **0.1.0** milestone targeted for **October 1, 2026**. These
targets are mirrored in `ROADMAP.md`, `STATUS.md`, and
`docs/release_plan.md`. See

[ROADMAP.md](ROADMAP.md) for feature milestones and
[docs/release_plan.md](docs/release_plan.md) for the full schedule,
outstanding tasks, and current test and coverage status. The release
workflow is detailed in [docs/releasing.md](docs/releasing.md).

## Status

See [STATUS.md](STATUS.md) for current test results; coverage is unavailable
while checks fail.
Task-level progress and test reconciliation live in
[TASK_PROGRESS.md](TASK_PROGRESS.md).

See [docs/release_plan.md](docs/release_plan.md#alpha-release-checklist) for the
alpha release checklist.

## Issue tracking

Work items are tracked in-repo under [`issues/`](issues). Tickets follow
the template and naming conventions in
[`issues/README.md`](issues/README.md). File names are slugged titles
without numeric prefixes. When a ticket is complete, set its `Status` to
`Archived` and move the file to [`issues/archive/`](issues/archive)
without renaming.

## Installation

See [docs/installation.md](docs/installation.md) for the authoritative
installation guide, including environment setup, optional features and
upgrade instructions.

### Optional extras

Heavy groups such as `nlp`, `distributed`, `analysis`, and `llm` pull large
dependencies and are not synced by `task verify`.

Autoresearch exposes optional extras to enable additional features:

- `nlp` – language processing via spaCy and BERTopic
- `ui` – reference Streamlit interface
- `vss` – DuckDB VSS extension for vector search
- `git` – local Git repository search
- `distributed` – Ray and Redis for distributed processing
- `analysis` – Polars-based data analysis utilities
- `llm` – heavy LLM libraries like `sentence-transformers`
- `parsers` – PDF and DOCX document ingestion
- `full` – installs `nlp`, `ui`, `vss`, `git`, `distributed`,
  `analysis`, `llm`, and `parsers`

Install extras with `uv sync --extra <name>` or
`pip install "autoresearch[<name>]"`. Examples:

```bash
uv sync --extra nlp          # language processing
uv sync --extra ui           # Streamlit interface
uv sync --extra distributed  # Ray and Redis
uv sync --extra llm          # LLM libraries
```

## Building the documentation

Install MkDocs and generate the static site:

```bash
uv pip install mkdocs
mkdocs build
```

Use `mkdocs serve` to preview the documentation locally.

## Accessibility

CLI output uses Markdown headings and plain-text lists so screen readers can
navigate sections. Help messages avoid color-only cues and respect the
`NO_COLOR` environment variable for ANSI-free output.
