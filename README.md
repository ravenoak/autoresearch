# Autoresearch

Autoresearch is a local-first research assistant that coordinates multiple agents to
produce evidence-backed answers. It uses a dialectical reasoning process and stores all
data in local databases so that searches and knowledge graphs remain on your machine.
The project is built around a modular Python package located under `src/autoresearch/`.
CLI utilities are provided via Typer and the HTTP API is powered by FastAPI.

## Installation

You can install the project dependencies with either **Poetry** or **pip**.

### Using Poetry
```bash
poetry install
```

### Using pip
```bash
pip install -e .
```

## Quick start

Run a search from the command line:
```bash
autoresearch search "What is quantum computing?"
```

Start the HTTP API with Uvicorn:
```bash
uvicorn autoresearch.api:app --reload
```
Send a query and check collected metrics:
```bash
curl -X POST http://localhost:8000/query -d '{"query": "Explain machine learning"}' -H "Content-Type: application/json"
curl http://localhost:8000/metrics
```

### Configuration hot reload

When you run any CLI command, Autoresearch starts watching `autoresearch.toml`
and `.env` for changes. Updates to these files are picked up automatically and
the configuration is reloaded on the fly. The watcher shuts down gracefully when
the process exits.

A starter configuration is available under [`examples/autoresearch.toml`](examples/autoresearch.toml).

For a detailed breakdown of the requirements and architecture, see
[docs/requirements.md](docs/requirements.md) and
[docs/specification.md](docs/specification.md).

## Development setup

Install the development dependencies:

```bash
poetry install --with dev
```

Alternatively you can run the helper script:

```bash
./scripts/setup.sh
```

This installs tools such as `flake8`, `mypy`, `pytest` and `tomli_w` which is
used to write TOML files during testing.

## Running tests

Execute all tests once the development environment is ready:

```bash
poetry run flake8 src tests
poetry run mypy src
poetry run pytest
poetry run pytest tests/behavior
```

### Troubleshooting

- If tests fail with `ModuleNotFoundError`, ensure all dependencies are installed using `pip install -e .` or `poetry install --with dev`.
- When starting the API with `uvicorn autoresearch.api:app --reload`, install `uvicorn` if the command is not found and verify that port `8000` is free.

## Building the documentation

Install MkDocs and generate the static site:

```bash
pip install mkdocs
mkdocs build
```

Use `mkdocs serve` to preview the documentation locally.

## Accessibility

CLI output uses Markdown headings and plain-text lists so screen readers can navigate sections. Help messages avoid color-only cues and respect the `NO_COLOR` environment variable for ANSI-free output.
