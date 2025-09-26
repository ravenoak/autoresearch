# Autoresearch

Autoresearch is a local-first research assistant that coordinates multiple agents to
produce evidence-backed answers. It uses a dialectical reasoning process and stores all
data in local databases so that searches and knowledge graphs remain on your machine.
The project is built around a modular Python package located under `src/autoresearch/`.
CLI utilities are provided via Typer and the HTTP API is powered by FastAPI.

**Note:** [docs/installation.md](docs/installation.md) is the authoritative
source for environment setup and optional features. After installing the
prerequisites, run `./scripts/setup.sh` to verify tooling, install
dependencies, and persist a PATH helper at `.autoresearch/path.sh`. New
shells can run `eval "$(./scripts/setup.sh --print-path)"` or source that
snippet to expose `.venv/bin` without re-running the installer. You can still
call `uv sync --extra test --extra docs` manually, but the setup script
guarantees Go Task is present and installs dependencies such as `pytest-bdd`,
which suppresses `PytestConfigWarning` messages and prevents missing plugin
errors during test and documentation commands.

Run `scripts/codex_setup.sh` in the Codex evaluation environment to bootstrap
dependencies. It shares the same PATH helper so `task` is available in new
shells immediately after it finishes.

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
- [Go Task](https://taskfile.dev/) 3.44.1+ (verify with `task --version`)

After installing the prerequisites, run `task install` to sync the
`dev-minimal` and `test` extras before executing any tests or `task`
commands.

Run `uv run python scripts/check_env.py` to confirm they are available. The
script exits with an error when Go Task is missing and suggests installing it
with `scripts/setup.sh` or your package manager. If a tool or package is
reported missing, rerun `task install` or sync optional extras with
`uv sync --extra <name>`. Run the setup script and verify Go Task with
`task --version`. The generated `.autoresearch/path.sh` keeps `.venv/bin` on
`PATH` for new shells; use the inline command to load it immediately:

```bash
./scripts/setup.sh
eval "$(./scripts/setup.sh --print-path)"
task --version
task check
```

`scripts/setup.sh` verifies the Python version, installs Go Task into
`/usr/local/bin` when needed, confirms `uv` is functional, and syncs the
`dev-minimal` and `test` extras. It exits with an error if a tool is missing or
the dependency sync fails. If installation fails, see `docs/installation.md`
for manual steps or package manager commands.

Optional extras provide features such as NLP, a UI, or distributed
processing. Install them on demand with `uv sync --extra <name>`, `task
install EXTRAS="<name>"`, or `pip install "autoresearch[<name>]"`. LLM
capabilities depend on the `llm` extra and are skipped unless you enable it.

## Depth-aware output controls

The `autoresearch search` command accepts a repeatable `--depth` flag that
reveals progressively richer sections of the final answer. Choose from the
following layers:

- `tldr` – prepend a concise summary of the answer.
- `findings` – list key findings distilled from the reasoning steps.
- `claims` – render a structured claim table with confidence and evidence.
- `trace` – print the execution trace captured by the audit log.
- `full` – enable every layer in a single flag.

For example, `autoresearch search "What changed?" --depth tldr --depth trace`
prints the standard report plus a TL;DR block and the recorded agent trace. The
JSON renderer attaches the same information under a `depth_sections` field so
automation can inspect the additional artifacts.

The Streamlit UI exposes matching controls in the query form. Toggle the depth
layers to tailor the answer and review evidence in the new **Provenance** tab,
which surfaces audit trail details and GraphRAG artifacts alongside the
knowledge graph.

### Enabling heavy extras

`task verify` syncs the `dev-minimal` and `test` extras by default.
Heavy groups such as `nlp`, `distributed`, `analysis`, and `llm` require
additional dependencies and must be enabled explicitly:

```bash
task verify EXTRAS="dev-minimal test nlp distributed"
```

For a lightweight iteration that avoids reinstalling optional extras, pin the
verify task to the default groups. This skips heavy packages that may have been
synced in previous sessions:

```bash
task verify EXTRAS="dev-minimal test"
```

`task verify:warnings` runs the same pipeline with `DeprecationWarning`
promoted to errors. Run it after `task install` (or any sync that includes the
`dev-minimal` and `test` extras) so plugins like `pytest-bdd` stay available.

Use the same `EXTRAS` flag with `task install` to sync them for local
development. Include `EXTRAS="llm"` when verifying or installing LLM
libraries; the environment check skips them otherwise. Run `task check
EXTRAS="llm"` when editing LLM code so lint and smoke tests have
`dspy-ai` and `fastembed` available.

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

Before running those commands in a fresh terminal, load the helper with
`source .autoresearch/path.sh` (or `eval "$(./scripts/setup.sh --print-path)"`)
so Go Task and the virtual environment are available without re-running
`scripts/setup.sh`.

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
expects for quick smoke tests. Missing `pytest-bdd` triggers
`PytestConfigWarning` notices about undefined BDD markers. Install it before
`pytest` to mirror the DuckDB setup performed by `scripts/setup.sh` and let `uv`
run `pytest` succeed without `task`.

Run `task check` for linting, type checks, and quick smoke tests. It syncs the
`dev-minimal` and `test` extras and exercises a small unit subset
(`test_version` and `test_cli_help`) for fast feedback. `task verify` runs the
full suite and installs the `dev-minimal` and `test` extras by default.
Pass `EXTRAS="dev-minimal test distributed analysis"` or similar when invoking
the command to include heavy groups.

See [Full extras verification](docs/testing_guidelines.md#full-extras-verification)
for the workflow that checks representative imports, hydrates GPU wheels, and
runs `task verify` with every optional extra.

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

PDF and DOCX ingestion is in-scope for the 0.1.0a1 milestone when the
`parsers` extra is installed. The dedicated parser module normalizes text
and raises explicit errors for corrupt files so the local file backend and
cache stay deterministic.

Install extras with `uv sync --extra <name>` or
`pip install "autoresearch[<name>]"`. Examples:

```bash
uv sync --extra nlp          # language processing
uv sync --extra ui           # Streamlit interface
uv sync --extra distributed  # Ray and Redis
uv sync --extra parsers      # PDF and DOCX ingestion for local files
uv sync --extra llm          # LLM libraries
```

## Building the documentation

Sync the documentation dependencies and build the static site:

```bash
uv sync --extra docs
task docs
```

Run `uv run --extra docs mkdocs build` directly if you skip Go Task, and use
`uv run mkdocs serve` to preview the documentation locally.

## Accessibility

CLI output uses Markdown headings and plain-text lists so screen readers can
navigate sections. Help messages avoid color-only cues and respect the
`NO_COLOR` environment variable for ANSI-free output.
