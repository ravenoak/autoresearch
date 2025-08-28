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

## Prerequisites

Autoresearch requires **Python 3.12+**,
[uv](https://github.com/astral-sh/uv), and
[Go Task](https://taskfile.dev/). Running `task install` automatically downloads
`task` to `.venv/bin` when it's missing; the same check occurs in
`./scripts/setup.sh` during a full developer bootstrap. See
[docs/installation.md#after-cloning](docs/installation.md#after-cloning) for
details.

Install Go Task manually if needed:

```bash
curl -sSL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin
# macOS: brew install go-task/tap/go-task
```

Optional extras provide features such as NLP, a UI, or distributed
processing. Install them on demand with `uv sync --extra <name>` or
`pip install "autoresearch[<name>]"`.

A running Redis server is needed only for the `[distributed]` extra or tests
tagged `requires_distributed`. The test suite's `redis_client` fixture connects
to a local server or starts a lightweight `fakeredis` instance. When neither
service is available those scenarios are skipped. Run the distributed tests
with:

```bash
uv run pytest -m requires_distributed -q
```

To bootstrap a Python 3.12+ environment with the lightweight development and test
extras run:

```bash
task install
```

This syncs the `dev-minimal` and `test` extras to install tools like
`pytest-httpx`, `duckdb`, and `networkx` needed for local testing.

Run `task check` for linting and a fast subset of unit tests; it syncs only the
`dev-minimal` extra. For the full suite, including integration and behavior
tests, run `task verify` after syncing the `test` extra (the default behavior of
`task install`).

For current capabilities and known limitations see
[docs/release_notes.md](docs/release_notes.md).

## Roadmap

As of **August 26, 2025**, Autoresearch is in the **Development** phase
preparing for the upcoming **0.1.0** release. The version is defined in
`autoresearch.__version__` and mirrored in `pyproject.toml`, but it has
**not** been published yet. The first official release was originally
planned for **July 20, 2025**, but the schedule slipped. An
**0.1.0-alpha.1** preview is re-targeted for **2026-06-15**, with
the final **0.1.0** milestone targeted for **July 1, 2026**. See

[ROADMAP.md](ROADMAP.md) for feature milestones and
[docs/release_plan.md](docs/release_plan.md) for the full schedule,
outstanding tasks, and current test and coverage status. The release
workflow is detailed in [docs/releasing.md](docs/releasing.md).

## Status

See [STATUS.md](STATUS.md) for current test results and **91%** coverage.
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

Autoresearch exposes optional extras to enable additional features:

- `nlp` – language processing via spaCy and BERTopic
- `llm` – heavy LLM libraries like `sentence-transformers`
- `parsers` – PDF and DOCX document ingestion
- `ui` – reference Streamlit interface
- `vss` – DuckDB VSS extension for vector search
- `distributed` – Ray and Redis for distributed processing
- `analysis` – Polars-based data analysis utilities
- `git` – local Git repository search
- `full` – installs `nlp`, `ui`, `vss`, `distributed`, and `analysis`

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
