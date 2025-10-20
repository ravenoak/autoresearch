# Optional Extras Documentation

## Overview

Autoresearch ships with optional dependency groups ("extras") so you can
install only the features you need. Sync extras with `uv sync --extra <name>`,
`task install EXTRAS="<name>"`, or `pip install "autoresearch[<name>]"`.

## Desktop experience (`desktop`)

The `desktop` extra provides the PySide6-powered native user interface. Install
it with `uv sync --extra desktop` (or `pip install "autoresearch[desktop]")`
and launch the UI with `autoresearch desktop`.

### Dependencies

- PySide6 and Qt WebEngine
- Rich logging, packaging, and config helpers shared with the CLI
- Test fixtures for window management and widget smoke tests

### Features

- Dockable multi-pane workspace driven by `AutoresearchMainWindow`
- Embedded configuration editor with live JSON validation
- Session timeline and quick resume support via `SessionManager`
- Knowledge graph visualization backed by Qt's scene graph
- Export manager for GraphML, JSON, and other storage integrations
- Metrics dashboard and run inspector widgets for rapid debugging

### Recommended workflow

1. `uv sync --extra desktop`
2. `autoresearch desktop`
3. Configure sources and credentials inside the desktop settings panel
4. Use the session switcher to resume previous investigations

`task check EXTRAS="desktop"` runs smoke tests that import PySide6 widgets to
confirm the UI stack is available.

## Core development extras

- `dev-minimal`: Formatting, linting, and fast test dependencies
- `test`: Full test suite requirements, including `pytest-bdd`

## Feature extras

- `analysis`: Data exploration with Polars and Matplotlib
- `distributed`: Ray and Redis for multi-process orchestration
- `git`: Git repository mining via GitPython
- `gpu`: GPU-enabled embeddings and BERTopic pipelines
- `llm`: CPU-friendly LLM integrations such as `dspy-ai` and `fastembed`
- `nlp`: spaCy models and text analysis utilities
- `parsers`: PDF, DOCX, and HTML ingestion libraries
- `vss`: DuckDB vector search extension management

Install multiple extras at once:

```bash
uv sync --extra desktop --extra nlp --extra parsers
```

Run targeted tests using the matching pytest markers (e.g.,
`uv run pytest -m requires_nlp`).

## Legacy maintenance

The Streamlit-based interface now lives behind the `ui` extra. It remains
available for teams that need to keep the web dashboard running during the
migration to the desktop workflow.

- Install with `uv sync --extra ui`
- Review [docs/specs/streamlit-refactor-plan.md](docs/specs/streamlit-refactor-plan.md)
  before enabling it
- Launch with `uv run streamlit run streamlit_app.py`
- Run targeted tests with `uv run pytest -m requires_ui`

Prefer the `desktop` extra for new deployments so the `autoresearch desktop`
entry point stays aligned with current development.

## Build and release extras

- `build`: Wheel and source distribution tooling (build, twine, cibuildwheel)
- `dev`: Full developer workstation toolchain
- `full`: Convenience group that installs every optional feature

## Troubleshooting

Missing extra dependencies trigger import errors or skipped tests. Sync the
needed group and rerun the command:

```bash
uv sync --extra llm
uv run pytest -m requires_llm
```

For GPU installations, pre-populate `wheels/gpu` with platform-compatible
artifacts to avoid source builds.
