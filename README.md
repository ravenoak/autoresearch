# Autoresearch

Autoresearch is a local-first research assistant that coordinates multiple agents to
produce evidence-backed answers. It uses a dialectical reasoning process and stores all
data in local databases so that searches and knowledge graphs remain on your machine.
The project is built around a modular Python package located under `src/autoresearch/`.
CLI utilities are provided via Typer and the HTTP API is powered by FastAPI.

**Note:** [docs/installation.md](docs/installation.md) is the authoritative
source for environment setup and optional features.

## Prerequisites

Autoresearch requires **Python 3.12+**,
[uv](https://github.com/astral-sh/uv), and
[Go Task](https://taskfile.dev/). For detailed setup instructions, see
[docs/installation.md](docs/installation.md).

For current capabilities and known limitations see
[docs/release_notes.md](docs/release_notes.md).

## Roadmap

As of **August 18, 2025**, Autoresearch is in the **Development** phase
preparing for the upcoming **0.1.0** release. The version is defined in
`autoresearch.__version__` and mirrored in `pyproject.toml`, but it has
**not** been published yet. The first official release was originally
planned for **July 20, 2025**, but the schedule slipped. An
**0.1.0-alpha.1** preview is scheduled for **2026-03-01**, with
the final **0.1.0** milestone targeted for **July 1, 2026**. See
[ROADMAP.md](ROADMAP.md) for feature milestones and
[docs/release_plan.md](docs/release_plan.md) for the full schedule,
outstanding tasks, and current test and coverage status. The release
workflow is detailed in [docs/releasing.md](docs/releasing.md).

Current checks show `uv run --extra dev-minimal flake8 src tests` and
`uv run --extra dev-minimal mypy src` passing. `uv run --extra
dev-minimal pytest -q --cov=src --cov-report=term` returns failing tests
with total coverage around 67%.

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

## Building the documentation

Install MkDocs and generate the static site:

```bash
uv pip install mkdocs
mkdocs build
```

Use `mkdocs serve` to preview the documentation locally.

## Accessibility

CLI output uses Markdown headings and plain-text lists so screen readers can navigate sections. Help messages avoid color-only cues and respect the `NO_COLOR` environment variable for ANSI-free output.
